"""HolographicMemory — ties the encoder, the SDM engine and persistence together
and implements the four MCP tool operations.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from .encoder import encode, hamming
from .sdm import SDM


@dataclass
class Snapshot:
    id: str
    fact: str
    context: str = ""
    importance: float = 0.5
    valence: str = "neutral"
    tags: list[str] = field(default_factory=list)
    created_at: int = 0
    access_count: int = 0
    last_used: int = 0


def _now() -> int:
    return int(time.time())


class HolographicMemory:
    def __init__(
        self,
        path: str | Path,
        *,
        dim: int = 10000,
        num_locations: int = 1024,
        activation_k: int = 32,
    ):
        self.path = Path(path).expanduser()
        self.path.mkdir(parents=True, exist_ok=True)
        self.dim = dim
        self.snapshots: list[Snapshot] = []
        self.vectors = np.zeros((0, dim), dtype=np.uint8)
        self.sdm = SDM(dim, num_locations, activation_k)
        self._load()

    # ---- persistence -------------------------------------------------
    @property
    def _meta_file(self) -> Path:
        return self.path / "snapshots.json"

    def _load(self) -> None:
        addr = self.path / "addresses.npy"
        cnt = self.path / "counters.npy"
        vec = self.path / "vectors.npy"
        if addr.exists():
            self.sdm.addresses = np.load(addr)
        if cnt.exists():
            self.sdm.counters = np.load(cnt)
        if vec.exists():
            self.vectors = np.load(vec)
        if self._meta_file.exists():
            data = json.loads(self._meta_file.read_text("utf-8"))
            self.snapshots = [Snapshot(**s) for s in data]

    def save(self) -> None:
        np.save(self.path / "addresses.npy", self.sdm.addresses)
        np.save(self.path / "counters.npy", self.sdm.counters)
        np.save(self.path / "vectors.npy", self.vectors)
        self._meta_file.write_text(
            json.dumps([asdict(s) for s in self.snapshots], ensure_ascii=False), "utf-8"
        )

    # ---- tool operations --------------------------------------------
    def store_snapshot(
        self,
        fact: str,
        context: str = "",
        importance: float = 0.5,
        valence: str = "neutral",
        tags: list[str] | None = None,
    ) -> dict:
        tags = tags or []
        vec = encode(" ".join([fact, context, *tags]), self.dim)
        snap = Snapshot(
            id=uuid.uuid4().hex[:12],
            fact=fact,
            context=context,
            importance=float(importance),
            valence=valence,
            tags=tags,
            created_at=_now(),
            last_used=_now(),
        )
        self.snapshots.append(snap)
        self.vectors = np.vstack([self.vectors, vec]) if self.vectors.size else vec[None, :]
        self.sdm.write(vec, vec)  # autoassociative superposition
        self.save()
        return {"id": snap.id, "stored": True, "total_memories": len(self.snapshots)}

    def recall(self, query: str, top_k: int = 5, association_depth: int = 2) -> dict:
        if not self.snapshots:
            return {"results": [], "note": "memory is empty"}
        q = encode(query, self.dim)
        denoised = self.sdm.read(q)  # holographic clean-up
        # blend the raw cue with the SDM-reconstructed signal
        score = 0.5 * hamming(self.vectors, q) + 0.5 * hamming(self.vectors, denoised)
        pool = min(len(self.snapshots), max(top_k, top_k * max(1, association_depth)))
        order = np.argsort(score)[:pool][:top_k]
        results = []
        for i in order:
            s = self.snapshots[int(i)]
            s.access_count += 1
            s.last_used = _now()
            results.append(
                {
                    "fact": s.fact,
                    "context": s.context,
                    "tags": s.tags,
                    "importance": s.importance,
                    "similarity": round(1 - score[int(i)] / self.dim, 3),
                }
            )
        self.save()
        return {"results": results}

    def interference(self, new_fact: str, threshold: float = 0.55) -> dict:
        if not self.snapshots:
            return {"conflict_detected": False}
        v = encode(new_fact, self.dim)
        dist = hamming(self.vectors, v)
        i = int(np.argmin(dist))
        sim = 1 - dist[i] / self.dim
        if sim >= threshold and sim < 0.999:
            return {
                "conflict_detected": True,
                "previous_memory": self.snapshots[i].fact,
                "confidence": round(float(sim), 2),
                "hint": "The new fact strongly overlaps an existing one — confirm before overwriting.",
            }
        return {"conflict_detected": False, "closest_similarity": round(float(sim), 3)}

    def consolidate(self, max_loss_tolerance: float = 0.1) -> dict:
        before = len(self.snapshots)
        if before == 0:
            return {"removed": 0, "remaining": 0}
        scores = np.array([s.importance * 10 + s.access_count for s in self.snapshots], dtype=float)
        drop = int(round(before * float(max_loss_tolerance)))
        if drop <= 0:
            return {"removed": 0, "remaining": before}
        weak = set(np.argsort(scores)[:drop].tolist())
        keep = [i for i in range(before) if i not in weak]
        self.snapshots = [self.snapshots[i] for i in keep]
        self.vectors = self.vectors[keep] if keep else np.zeros((0, self.dim), dtype=np.uint8)
        # rebuild the distributed trace from survivors
        self.sdm.reset_counters()
        for vec in self.vectors:
            self.sdm.write(vec, vec)
        self.save()
        return {"removed": before - len(self.snapshots), "remaining": len(self.snapshots)}
