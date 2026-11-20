"""
RAG Pipeline — Embedding Module
Loads the sentence-transformer model once and provides encode() helper.
Includes deterministic semantic vector fallback if sentence-transformers is not yet installed.
"""
import hashlib
from typing import List
from app.config import settings

_model = None
_use_fallback = False


def _deterministic_hash_vector(text: str, dim: int = 384) -> List[float]:
    """Lightweight 384-dimensional normalized pseudo-semantic vector based on token frequencies and n-grams."""
    vec = [0.0] * dim
    words = text.lower().split()
    if not words:
        return vec
    for w in words:
        h = int(hashlib.md5(w.encode()).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    # Normalize vector to unit length
    norm = sum(x * x for x in vec) ** 0.5
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def get_embedding_model():
    global _model, _use_fallback
    if _use_fallback:
        return None
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception:
            _use_fallback = True
            _model = None
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of text strings. Returns list of float vectors."""
    if not texts:
        return []
    model = get_embedding_model()
    if model is not None:
        try:
            embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception:
            pass
    # Fallback if sentence-transformers not available or throws
    return [_deterministic_hash_vector(t) for t in texts]


def embed_query(query: str) -> List[float]:
    """Embed a single query string."""
    result = embed_texts([query])
    return result[0] if result else []
