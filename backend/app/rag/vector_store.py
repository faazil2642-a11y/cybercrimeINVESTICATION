"""
RAG Pipeline — ChromaDB Vector Store
Manages persistent collections:
  - cybertrace_case_evidence (per-case, filtered by case_id metadata)
  - cybertrace_knowledge (global knowledge base)
Includes memory store fallback if chromadb is not yet installed.
"""
import uuid
import math
from typing import List, Dict, Any, Optional
from app.config import settings

_client = None
_collections: Dict[str, Any] = {}
_fallback_store: Dict[str, List[Dict[str, Any]]] = {
    "cybertrace_case_evidence": [],
    "cybertrace_knowledge": []
}

EVIDENCE_COLLECTION = "cybertrace_case_evidence"
KNOWLEDGE_COLLECTION = "cybertrace_knowledge"


def get_chroma_client():
    global _client
    if _client is None:
        try:
            import chromadb
            _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        except Exception:
            _client = False
    return _client


def get_collection(collection_name: str):
    client = get_chroma_client()
    if not client:
        return None
    global _collections
    if collection_name not in _collections:
        _collections[collection_name] = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
    return _collections[collection_name]


def upsert_chunks(
    chunks: List[Dict[str, Any]],
    collection_name: str = EVIDENCE_COLLECTION,
) -> List[str]:
    """
    Insert chunks into ChromaDB. Each chunk has 'content' and 'metadata'.
    Returns list of chunk IDs inserted.
    """
    if not chunks:
        return []

    from app.rag.embeddings import embed_texts

    ids = [str(uuid.uuid4()) for _ in chunks]
    texts = [c["content"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # Sanitize metadata
    sanitized_metas = []
    for m in metadatas:
        sanitized = {}
        for k, v in m.items():
            if v is None:
                sanitized[k] = ""
            elif isinstance(v, (str, int, float, bool)):
                sanitized[k] = v
            else:
                sanitized[k] = str(v)
        sanitized_metas.append(sanitized)

    embeddings = embed_texts(texts)

    collection = get_collection(collection_name)
    if collection:
        try:
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=sanitized_metas,
            )
            return ids
        except Exception:
            pass

    # Fallback in-memory store
    if collection_name not in _fallback_store:
        _fallback_store[collection_name] = []
    for chunk_id, doc, meta, emb in zip(ids, texts, sanitized_metas, embeddings):
        _fallback_store[collection_name].append({
            "id": chunk_id,
            "document": doc,
            "metadata": meta,
            "embedding": emb
        })
    return ids


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def query_collection(
    query_embedding: List[float],
    collection_name: str,
    n_results: int = 5,
    where: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """
    Query ChromaDB with an embedding vector.
    Returns list of result dicts with content, metadata, distance.
    """
    collection = get_collection(collection_name)
    if collection:
        try:
            count = collection.count()
            if count == 0:
                return []
            kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": min(n_results, count),
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                kwargs["where"] = where
            results = collection.query(**kwargs)
            if results and results.get("ids") and results["ids"][0]:
                output = []
                ids = results["ids"][0]
                docs = results["documents"][0]
                metas = results["metadatas"][0]
                distances = results["distances"][0]
                for chunk_id, doc, meta, dist in zip(ids, docs, metas, distances):
                    similarity = 1.0 - dist
                    output.append({
                        "chunk_id": chunk_id,
                        "content": doc,
                        "metadata": meta,
                        "distance": dist,
                        "similarity": round(similarity, 4),
                    })
                return output
        except Exception:
            pass

    # Fallback in-memory search with case_id filtering
    candidates = _fallback_store.get(collection_name, [])
    if where:
        candidates = [
            c for c in candidates
            if all(c["metadata"].get(k) == v for k, v in where.items())
        ]

    scored = []
    for c in candidates:
        sim = _cosine_similarity(query_embedding, c.get("embedding", []))
        scored.append({
            "chunk_id": c["id"],
            "content": c["document"],
            "metadata": c["metadata"],
            "distance": round(1.0 - sim, 4),
            "similarity": round(sim, 4),
        })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:n_results]


def delete_by_evidence(evidence_id: str) -> None:
    """Remove all chunks for a specific evidence file."""
    try:
        collection = get_collection(EVIDENCE_COLLECTION)
        if collection:
            collection.delete(where={"evidence_id": evidence_id})
    except Exception:
        pass
    if EVIDENCE_COLLECTION in _fallback_store:
        _fallback_store[EVIDENCE_COLLECTION] = [
            c for c in _fallback_store[EVIDENCE_COLLECTION]
            if c["metadata"].get("evidence_id") != evidence_id
        ]


def get_collection_stats() -> Dict[str, int]:
    try:
        col_ev = get_collection(EVIDENCE_COLLECTION)
        col_kn = get_collection(KNOWLEDGE_COLLECTION)
        if col_ev and col_kn:
            return {
                EVIDENCE_COLLECTION: col_ev.count(),
                KNOWLEDGE_COLLECTION: col_kn.count(),
            }
    except Exception:
        pass
    return {
        EVIDENCE_COLLECTION: len(_fallback_store.get(EVIDENCE_COLLECTION, [])),
        KNOWLEDGE_COLLECTION: len(_fallback_store.get(KNOWLEDGE_COLLECTION, [])),
    }
