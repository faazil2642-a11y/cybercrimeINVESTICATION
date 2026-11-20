import hashlib
import os
import shutil
from pathlib import Path


def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file without loading it all into memory."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_record_hash(content: str, previous_hash: str = "") -> str:
    """Create a chained hash for chain-of-custody records."""
    combined = f"{previous_hash}:{content}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def verify_file_integrity(file_path: str, expected_hash: str) -> bool:
    """Compare current file hash to stored hash. Returns True if intact."""
    if not os.path.exists(file_path):
        return False
    current = compute_sha256(file_path)
    return current == expected_hash


def safe_copy(src: str, dst: str) -> None:
    """Copy src to dst without modifying original."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
