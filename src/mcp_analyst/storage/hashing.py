"""Artifact hashing for reproducibility."""

import hashlib
from pathlib import Path


def compute_file_hash(filepath: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        filepath: Path to file

    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_string_hash(content: str) -> str:
    """
    Compute SHA-256 hash of a string.

    Args:
        content: String content

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(content.encode()).hexdigest()

