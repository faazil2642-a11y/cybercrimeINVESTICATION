"""
RAG Pipeline — Chunking Module
Splits extracted text into overlapping chunks with line-number metadata.
"""
from typing import List, Dict, Any
from app.config import settings


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
    document_id: str = "",
    evidence_id: str = "",
    case_id: str = "",
    filename: str = "",
    collection_type: str = "cybertrace_case_evidence",
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks with metadata.
    Returns list of dicts with 'content' and 'metadata'.
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP

    if not text or not text.strip():
        return []

    lines = text.splitlines(keepends=True)
    chunks = []
    chunk_index = 0
    current_chars = 0
    current_lines: List[str] = []
    start_line = 1

    for line_num, line in enumerate(lines, 1):
        current_lines.append(line)
        current_chars += len(line)

        if current_chars >= chunk_size:
            content = "".join(current_lines).strip()
            if content:
                # Detect page number from common PDF page markers
                page_number = _detect_page_number(content)
                chunks.append({
                    "content": content,
                    "metadata": {
                        "document_id": document_id,
                        "evidence_id": evidence_id,
                        "case_id": case_id,
                        "filename": filename,
                        "collection_type": collection_type,
                        "chunk_index": chunk_index,
                        "line_start": start_line,
                        "line_end": line_num,
                        "page_number": page_number,
                    },
                })
                chunk_index += 1

            # Apply overlap: keep last N characters worth of lines
            if overlap > 0:
                overlap_lines = []
                overlap_chars = 0
                for ol in reversed(current_lines):
                    overlap_chars += len(ol)
                    overlap_lines.insert(0, ol)
                    if overlap_chars >= overlap:
                        break
                current_lines = overlap_lines
                current_chars = sum(len(l) for l in current_lines)
                start_line = line_num - len(current_lines) + 1
            else:
                current_lines = []
                current_chars = 0
                start_line = line_num + 1

    # Flush remaining content
    if current_lines:
        content = "".join(current_lines).strip()
        if content:
            page_number = _detect_page_number(content)
            chunks.append({
                "content": content,
                "metadata": {
                    "document_id": document_id,
                    "evidence_id": evidence_id,
                    "case_id": case_id,
                    "filename": filename,
                    "collection_type": collection_type,
                    "chunk_index": chunk_index,
                    "line_start": start_line,
                    "line_end": len(lines),
                    "page_number": page_number,
                },
            })

    return chunks


def _detect_page_number(text: str) -> int | None:
    """Try to detect [PAGE N] marker inserted by PDF extractor."""
    import re
    match = re.search(r"\[PAGE\s+(\d+)\]", text)
    if match:
        return int(match.group(1))
    return None
