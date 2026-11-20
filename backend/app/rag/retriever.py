"""
RAG Pipeline — Full Orchestration Service
Coordinates: embed query → retrieve chunks → assemble context → generate → cite
"""
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from app.config import settings
from app.rag.embeddings import embed_query
from app.rag.vector_store import (
    query_collection, EVIDENCE_COLLECTION, KNOWLEDGE_COLLECTION
)
from app.rag.prompts import build_investigation_prompt
from app.rag.generator import generate_response
from app.rag.chunking import chunk_text
from app.rag.vector_store import upsert_chunks


def retrieve_for_case(
    question: str,
    case_id: str,
    top_k: int = None,
    threshold: float = None,
    include_knowledge: bool = True,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Retrieve relevant chunks for a question, filtered strictly to case_id.
    Returns (evidence_results, knowledge_results).
    """
    top_k = top_k or settings.RAG_TOP_K
    threshold = threshold or settings.RAG_SIMILARITY_THRESHOLD

    query_embedding = embed_query(question)

    # Case evidence — MUST filter by case_id metadata
    evidence_results = query_collection(
        query_embedding=query_embedding,
        collection_name=EVIDENCE_COLLECTION,
        n_results=top_k,
        where={"case_id": case_id},
    )
    evidence_results = [r for r in evidence_results if r["similarity"] >= threshold]

    knowledge_results = []
    if include_knowledge:
        knowledge_results = query_collection(
            query_embedding=query_embedding,
            collection_name=KNOWLEDGE_COLLECTION,
            n_results=min(3, top_k),
        )
        knowledge_results = [r for r in knowledge_results if r["similarity"] >= threshold]

    return evidence_results, knowledge_results


def build_context_string(results: List[Dict]) -> str:
    """Format retrieved chunks into a readable context block."""
    if not results:
        return "No relevant evidence retrieved."
    parts = []
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        filename = meta.get("filename", "unknown")
        line_start = meta.get("line_start", "")
        line_end = meta.get("line_end", "")
        similarity = r.get("similarity", 0)
        line_ref = f" (Lines {line_start}-{line_end})" if line_start else ""
        parts.append(
            f"[SOURCE {i}: {filename}{line_ref}, Relevance: {similarity:.3f}]\n{r['content']}"
        )
    return "\n\n".join(parts)


def parse_findings_from_response(response_text: str) -> List[Dict[str, str]]:
    """Extract structured FINDINGS from LLM response text."""
    findings = []
    # Look for numbered FINDING patterns
    pattern = re.compile(
        r"(?:FINDING\s+\d+[:\.]?\s*)([^\n]+)\n"
        r"(?:.*?[Ss]everity[:\s]+([A-Z]+).*?\n)?"
        r"(.*?)(?=FINDING\s+\d+|LIMITATIONS|$)",
        re.DOTALL,
    )
    for match in pattern.finditer(response_text):
        title = match.group(1).strip().rstrip(":")
        severity = match.group(2) or "MEDIUM"
        desc = match.group(3).strip()[:500]
        if title:
            findings.append({"title": title, "severity": severity, "description": desc, "evidence_reference": ""})

    return findings[:10]  # Cap at 10 findings


def parse_limitations(response_text: str) -> List[str]:
    """Extract limitations section from response."""
    if "LIMITATIONS" not in response_text.upper():
        return []
    parts = re.split(r"LIMITATIONS[:\s]*", response_text, flags=re.IGNORECASE)
    if len(parts) < 2:
        return []
    lim_text = parts[-1].strip()
    lines = [l.strip().lstrip("-•*").strip() for l in lim_text.splitlines() if l.strip()]
    return [l for l in lines if l][:5]


def build_citations(evidence_results: List[Dict]) -> List[Dict]:
    """Build source citation objects from retrieved chunks."""
    citations = []
    for r in evidence_results:
        meta = r.get("metadata", {})
        citations.append({
            "document_name": meta.get("filename", "unknown"),
            "evidence_id": meta.get("evidence_id", ""),
            "chunk_id": r.get("chunk_id", ""),
            "page_number": meta.get("page_number") or None,
            "line_start": meta.get("line_start") or None,
            "line_end": meta.get("line_end") or None,
            "relevance_score": r.get("similarity", 0.0),
            "excerpt": r["content"][:300] + ("..." if len(r["content"]) > 300 else ""),
        })
    return citations


def run_rag_pipeline(
    question: str,
    case_id: str,
    case_number: str = "",
    session_id: str = "",
    top_k: int = None,
    include_knowledge: bool = True,
    chat_history: str = "",
) -> Dict[str, Any]:
    """
    Full RAG pipeline. Returns structured response dict.
    Raises AINotConfiguredError if LLM not set up.
    """
    evidence_results, knowledge_results = retrieve_for_case(
        question=question,
        case_id=case_id,
        top_k=top_k,
        include_knowledge=include_knowledge,
    )

    evidence_context = build_context_string(evidence_results)
    knowledge_context = build_context_string(knowledge_results)

    prompt = build_investigation_prompt(
        question=question,
        evidence_context=evidence_context,
        knowledge_context=knowledge_context,
        case_number=case_number,
        chat_history=chat_history,
    )

    answer = generate_response(prompt, temperature=0.1)

    findings = parse_findings_from_response(answer)
    limitations = parse_limitations(answer)
    citations = build_citations(evidence_results)

    return {
        "answer": answer,
        "case_id": case_id,
        "session_id": session_id,
        "sources": citations,
        "findings": findings,
        "limitations": limitations,
        "created_at": datetime.now(timezone.utc),
    }


def index_document(
    text: str,
    document_id: str,
    evidence_id: str,
    case_id: str,
    filename: str,
    collection_name: str = EVIDENCE_COLLECTION,
) -> List[str]:
    """Chunk text and upsert into ChromaDB. Returns list of chunk IDs."""
    chunks = chunk_text(
        text=text,
        document_id=document_id,
        evidence_id=evidence_id,
        case_id=case_id,
        filename=filename,
        collection_type=collection_name,
    )
    if not chunks:
        return []
    return upsert_chunks(chunks, collection_name=collection_name)
