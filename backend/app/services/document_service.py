import os
import json
from pathlib import Path
from typing import Optional


SUPPORTED_TEXT_TYPES = {".txt", ".log", ".json", ".csv"}
SUPPORTED_RICH_TYPES = {".pdf", ".docx"}
ALL_SUPPORTED = SUPPORTED_TEXT_TYPES | SUPPORTED_RICH_TYPES


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def is_supported(filename: str) -> bool:
    return get_file_extension(filename) in ALL_SUPPORTED


def extract_text(file_path: str, original_filename: str) -> str:
    """
    Extract text from supported file types.
    Operates on a working copy — never on the original evidence file.
    Returns extracted text string.
    """
    ext = get_file_extension(original_filename)

    if ext == ".pdf":
        return _extract_pdf(file_path)
    elif ext == ".docx":
        return _extract_docx(file_path)
    elif ext == ".csv":
        return _extract_csv(file_path)
    elif ext == ".json":
        return _extract_json(file_path)
    elif ext in (".txt", ".log"):
        return _extract_text(file_path)
    else:
        return f"[Unsupported file type: {ext}. Text extraction not available.]"


def _extract_pdf(file_path: str) -> str:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        pages = []
        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            if text.strip():
                pages.append(f"[PAGE {page_num}]\n{text}")
        doc.close()
        return "\n\n".join(pages) if pages else "[PDF: No extractable text found]"
    except ImportError:
        return "[PDF extraction requires PyMuPDF. Install with: pip install pymupdf]"
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def _extract_docx(file_path: str) -> str:
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs) if paragraphs else "[DOCX: No text found]"
    except ImportError:
        return "[DOCX extraction requires python-docx. Install with: pip install python-docx]"
    except Exception as e:
        return f"[DOCX extraction error: {e}]"


def _extract_csv(file_path: str) -> str:
    try:
        import pandas as pd
        df = pd.read_csv(file_path, nrows=10000)
        return df.to_string(index=False)
    except ImportError:
        # Fallback: read as plain text
        return _extract_text(file_path)
    except Exception as e:
        return f"[CSV extraction error: {e}]\n" + _extract_text(file_path)


def _extract_json(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return _extract_text(file_path)


def _extract_text(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"[Text extraction error: {e}]"
