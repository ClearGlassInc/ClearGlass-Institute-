"""Entity resolution - collapse fragmented records into real identities.

Fraud hides in fragmentation: the same provider or patient appears under slightly
different names, a shared device, a recycled address. Without resolving those to
one identity, behavioural analytics is blind. This module does probabilistic
record linkage with an explainable, weighted score per field, then merges records
above a threshold using union-find - and reports a confidence for every merge so
an analyst (or a court) can see *why* two records were joined.

Standard library only; the scoring is deterministic and inspectable rather than a
black box, in keeping with ClearPulse's explainability-first stance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

# Per-field contribution to the [0, 1] match score. Tunable like the risk rules.
DEFAULT_WEIGHTS: dict[str, float] = {
    "name": 0.35,
    "dob": 0.25,
    "address": 0.20,
    "device": 0.15,
    "ssn_last4": 0.05,
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(value: Any) -> set[str]:
    return set(_TOKEN_RE.findall(str(value).lower())) if value is not None else set()


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def name_similarity(a: Any, b: Any) -> float:
    """Token Jaccard over normalised names (order/casing/punctuation agnostic)."""
    return _jaccard(_tokens(a), _tokens(b))


def dob_similarity(a: Any, b: Any) -> float:
    """1.0 for an exact date match, else 0.0 (DOB is high-precision when present)."""
    if not a or not b:
        return 0.0
    return 1.0 if str(a).strip() == str(b).strip() else 0.0


def address_similarity(a: Any, b: Any) -> float:
    return _jaccard(_tokens(a), _tokens(b))


def exact_similarity(a: Any, b: Any) -> float:
    if a is None or b is None:
        return 0.0
    return 1.0 if str(a).strip().lower() == str(b).strip().lower() else 0.0


@dataclass
class Record:
    """A raw identity record to be resolved (provider, patient, or staff)."""

    record_id: str
    attrs: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolvedEntity:
    """A merged cluster of records judged to be one real-world identity."""

    entity_id: str
    record_ids: list[str]
    confidence: float
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "record_ids": list(self.record_ids),
            "confidence": round(self.confidence, 3),
            "evidence": list(self.evidence),
        }


class _UnionFind:
    def __init__(self, items: list[str]) -> None:
        self.parent = {i: i for i in items}

    def find(self, x: str) -> str:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path halving
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


class EntityResolver:
    """Probabilistic record linkage with explainable, confidence-scored merges."""

    def __init__(
        self,
        weights: Optional[dict[str, float]] = None,
        *,
        threshold: float = 0.6,
    ) -> None:
        self.weights = weights or DEFAULT_WEIGHTS
        self.threshold = threshold
        self.records: dict[str, Record] = {}
        # Field -> similarity function. Unlisted fields fall back to exact match.
        self._sims = {
            "name": name_similarity,
            "dob": dob_similarity,
            "address": address_similarity,
            "device": exact_similarity,
            "ssn_last4": exact_similarity,
        }

    def add(self, record_id: str, attrs: dict[str, Any]) -> Record:
        rec = Record(record_id=record_id, attrs=dict(attrs))
        self.records[record_id] = rec
        return rec

    def score(self, a: Record, b: Record) -> tuple[float, list[str]]:
        """Weighted similarity in [0, 1] plus the per-field evidence behind it."""
        total = 0.0
        possible = 0.0
        evidence: list[str] = []
        for field_name, weight in self.weights.items():
            va, vb = a.attrs.get(field_name), b.attrs.get(field_name)
            if va is None or vb is None:
                continue  # missing on one side - do not penalise, just skip
            possible += weight
            sim = self._sims.get(field_name, exact_similarity)(va, vb)
            total += weight * sim
            if sim > 0:
                evidence.append(f"{field_name}~{sim:.2f}")
        if possible == 0:
            return 0.0, evidence
        # Normalise by the weight that was actually comparable, so two records
        # that share only one field are not unfairly capped.
        return total / possible, evidence

    def resolve(self) -> list[ResolvedEntity]:
        """Cluster records into entities; merges above ``threshold`` are joined.

        Confidence for a cluster is the minimum pairwise score among the merges
        that built it (the weakest link), which is the conservative number to put
        in front of an auditor.
        """
        ids = list(self.records)
        uf = _UnionFind(ids)
        cluster_scores: dict[tuple[str, str], tuple[float, list[str]]] = {}
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = self.records[ids[i]], self.records[ids[j]]
                sim, evidence = self.score(a, b)
                if sim >= self.threshold:
                    uf.union(ids[i], ids[j])
                    cluster_scores[(ids[i], ids[j])] = (sim, evidence)

        groups: dict[str, list[str]] = {}
        for rid in ids:
            groups.setdefault(uf.find(rid), []).append(rid)

        entities: list[ResolvedEntity] = []
        for root, members in sorted(groups.items()):
            members.sort()
            # Gather the merge scores/evidence internal to this cluster.
            scores = [s for (x, y), (s, _ev) in cluster_scores.items()
                      if uf.find(x) == root]
            evidence = sorted({e for (x, y), (_s, ev) in cluster_scores.items()
                               if uf.find(x) == root for e in ev})
            confidence = min(scores) if scores else 1.0  # singleton = trivially itself
            entities.append(ResolvedEntity(
                entity_id=f"E-{root}",
                record_ids=members,
                confidence=confidence,
                evidence=evidence,
            ))
        return entities
