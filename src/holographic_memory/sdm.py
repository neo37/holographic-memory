"""Kanerva Sparse Distributed Memory.

Facts are superposed across many hard locations (wave superposition); reads
collect the activated locations and reconstruct the signal by the majority rule
`sign(sum)`, which de-noises partial or noisy cues.

Activation uses k-nearest hard locations rather than a fixed Hamming radius so
that a meaningful set always fires regardless of vector statistics — a common
practical SDM variant.
"""
from __future__ import annotations

import numpy as np

_CLIP = 30000


class SDM:
    def __init__(
        self,
        dim: int,
        num_locations: int,
        activation_k: int,
        *,
        addresses: np.ndarray | None = None,
        counters: np.ndarray | None = None,
        seed: int = 42,
    ):
        self.dim = dim
        self.num_locations = num_locations
        self.activation_k = activation_k
        if addresses is None:
            addresses = np.random.default_rng(seed).integers(0, 2, size=(num_locations, dim), dtype=np.uint8)
        self.addresses = addresses
        self.counters = counters if counters is not None else np.zeros((num_locations, dim), dtype=np.int16)

    def _activate(self, addr: np.ndarray) -> np.ndarray:
        dist = np.count_nonzero(self.addresses != addr, axis=1)
        k = min(self.activation_k, self.num_locations)
        return np.argpartition(dist, k - 1)[:k]

    def write(self, addr: np.ndarray, data: np.ndarray) -> None:
        idx = self._activate(addr)
        delta = data.astype(np.int16) * 2 - 1  # {0,1} -> {-1,+1}
        self.counters[idx] += delta
        np.clip(self.counters, -_CLIP, _CLIP, out=self.counters)

    def read(self, addr: np.ndarray) -> np.ndarray:
        idx = self._activate(addr)
        acc = self.counters[idx].sum(axis=0)
        return (acc > 0).astype(np.uint8)

    def reset_counters(self) -> None:
        self.counters[:] = 0
