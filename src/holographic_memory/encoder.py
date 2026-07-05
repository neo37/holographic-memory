"""Text -> high-dimensional binary hypervector.

Each token maps to a deterministic random vector; a snapshot's vector is the
per-bit majority (bundle) of its token vectors. Texts that share vocabulary end
up close in Hamming space, which is what makes recall associative rather than
literal.
"""
from __future__ import annotations

import hashlib
import re

import numpy as np

_TOKEN_RE = re.compile(r"[^0-9a-zA-Zа-яА-ЯёЁ]+")


def _seed(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big")


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.split(text.lower()) if t]


def _token_vector(token: str, dim: int) -> np.ndarray:
    return np.random.default_rng(_seed(token)).integers(0, 2, size=dim, dtype=np.uint8)


def encode(text: str, dim: int) -> np.ndarray:
    tokens = tokenize(text)
    if not tokens:
        return np.random.default_rng(_seed(text or "∅")).integers(0, 2, size=dim, dtype=np.uint8)

    acc = np.zeros(dim, dtype=np.int32)
    for tok in tokens:
        acc += _token_vector(tok, dim).astype(np.int32) * 2 - 1  # bipolar vote

    out = (acc > 0).astype(np.uint8)
    ties = acc == 0
    if ties.any():
        tiebreak = np.random.default_rng(_seed("∥tie∥")).integers(0, 2, size=dim, dtype=np.uint8)
        out[ties] = tiebreak[ties]
    return out


def hamming(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    """Row-wise Hamming distance from every row of `matrix` to `vector`."""
    return np.count_nonzero(matrix != vector, axis=1)
