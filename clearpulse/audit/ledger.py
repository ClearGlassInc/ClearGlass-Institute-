"""Cryptographic audit chain - the forensic moat under ClearPulse.

ClearPulse already threads an immutable ``trace_id`` through every stage. This
module makes the *ledger itself* tamper-evident, turning "we log everything" into
"we can **prove** nothing was altered after the fact":

* Every event is sealed into a :class:`LedgerEntry` whose hash commits to the
  entry's content **and** the hash of the entry before it (a blockchain-style
  hash chain). Changing any historical entry breaks every hash after it, and
  :meth:`AuditChain.verify` pinpoints exactly where.
* A Merkle root over all entry hashes gives a single fixed-size commitment that
  can be published/notarised; :meth:`AuditChain.inclusion_proof` produces an
  O(log n) proof that a specific entry is in the ledger without revealing the
  rest - the primitive litigation and regulator workflows need.

Pure standard library (``hashlib`` + canonical JSON), so the evidence layer has
no external trust dependency and is fully unit-testable.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

GENESIS_PREV_HASH = "0" * 64


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_pair(left: str, right: str) -> str:
    """Hash two child hashes into a Merkle parent (order-significant)."""
    return _sha256_hex((left + right).encode("utf-8"))


@dataclass(frozen=True)
class LedgerEntry:
    """One sealed record in the audit chain.

    The ``entry_hash`` commits to every field above it plus ``prev_hash``; it is
    computed at construction and is what the next entry chains onto.
    """

    index: int
    timestamp: str
    event_type: str
    payload: dict[str, Any]
    trace_id: Optional[str]
    prev_hash: str
    entry_hash: str = field(default="")

    def digest(self) -> str:
        """Recompute this entry's hash from its content (excludes entry_hash).

        Canonical JSON (sorted keys, no whitespace) guarantees the same bytes are
        hashed on every machine, so a re-verification elsewhere matches exactly.
        """
        body = {
            "index": self.index,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "payload": self.payload,
            "trace_id": self.trace_id,
            "prev_hash": self.prev_hash,
        }
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"),
                               default=str)
        return _sha256_hex(canonical.encode("utf-8"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "payload": self.payload,
            "trace_id": self.trace_id,
            "prev_hash": self.prev_hash,
            "entry_hash": self.entry_hash,
        }


@dataclass
class VerificationResult:
    """Outcome of a full-chain verification."""

    ok: bool
    entries: int
    broken_index: Optional[int] = None
    reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "entries": self.entries,
            "broken_index": self.broken_index,
            "reason": self.reason,
        }


class AuditChain:
    """An append-only, hash-chained, Merkle-committed ledger of events."""

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    # -- writing ------------------------------------------------------------

    def append(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        trace_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> LedgerEntry:
        """Seal a new event onto the head of the chain and return its entry."""
        index = len(self._entries)
        prev_hash = self._entries[-1].entry_hash if self._entries else GENESIS_PREV_HASH
        draft = LedgerEntry(
            index=index,
            timestamp=timestamp or _utcnow_iso(),
            event_type=event_type,
            payload=dict(payload),
            trace_id=trace_id,
            prev_hash=prev_hash,
        )
        sealed = LedgerEntry(
            index=draft.index,
            timestamp=draft.timestamp,
            event_type=draft.event_type,
            payload=draft.payload,
            trace_id=draft.trace_id,
            prev_hash=draft.prev_hash,
            entry_hash=draft.digest(),
        )
        self._entries.append(sealed)
        return sealed

    # -- reading ------------------------------------------------------------

    @property
    def entries(self) -> list[LedgerEntry]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def head_hash(self) -> str:
        """The hash of the latest entry - a commitment to the whole history."""
        return self._entries[-1].entry_hash if self._entries else GENESIS_PREV_HASH

    # -- verification -------------------------------------------------------

    def verify(self) -> VerificationResult:
        """Recompute the chain end to end; locate the first break if any.

        Two invariants per entry: (1) its stored hash matches a fresh digest of
        its content (no field was edited), and (2) its ``prev_hash`` equals the
        previous entry's hash (no entry was inserted/removed/reordered).
        """
        prev = GENESIS_PREV_HASH
        for entry in self._entries:
            if entry.prev_hash != prev:
                return VerificationResult(
                    ok=False, entries=len(self._entries),
                    broken_index=entry.index,
                    reason="prev_hash mismatch (entry inserted/removed/reordered)")
            if entry.digest() != entry.entry_hash:
                return VerificationResult(
                    ok=False, entries=len(self._entries),
                    broken_index=entry.index,
                    reason="content hash mismatch (entry was altered)")
            prev = entry.entry_hash
        return VerificationResult(ok=True, entries=len(self._entries))

    # -- Merkle commitment --------------------------------------------------

    def _leaves(self) -> list[str]:
        return [e.entry_hash for e in self._entries]

    def merkle_root(self) -> str:
        """A single fixed-size commitment to every entry hash.

        Standard binary Merkle tree; an odd level duplicates its last node. The
        empty ledger commits to the genesis sentinel so a root always exists.
        """
        level = self._leaves()
        if not level:
            return GENESIS_PREV_HASH
        while len(level) > 1:
            if len(level) % 2 == 1:
                level.append(level[-1])
            level = [hash_pair(level[i], level[i + 1])
                     for i in range(0, len(level), 2)]
        return level[0]

    def inclusion_proof(self, index: int) -> list[tuple[str, str]]:
        """Merkle proof that entry ``index`` is committed by :meth:`merkle_root`.

        Returns a list of ``(sibling_hash, side)`` steps, where ``side`` is
        ``"left"``/``"right"`` indicating which side the sibling sits on. Feed it
        to :func:`verify_inclusion_proof` along with the leaf and the root.
        """
        if not (0 <= index < len(self._entries)):
            raise IndexError(f"no entry at index {index}")
        level = self._leaves()
        idx = index
        proof: list[tuple[str, str]] = []
        while len(level) > 1:
            if len(level) % 2 == 1:
                level.append(level[-1])
            if idx % 2 == 0:
                proof.append((level[idx + 1], "right"))
            else:
                proof.append((level[idx - 1], "left"))
            level = [hash_pair(level[i], level[i + 1])
                     for i in range(0, len(level), 2)]
            idx //= 2
        return proof

    # -- export -------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [e.to_dict() for e in self._entries],
            "head_hash": self.head_hash,
            "merkle_root": self.merkle_root(),
            "length": len(self._entries),
        }


def verify_inclusion_proof(
    leaf_hash: str, proof: list[tuple[str, str]], root: str,
) -> bool:
    """Recompute a Merkle root from a leaf + proof and compare to ``root``."""
    computed = leaf_hash
    for sibling, side in proof:
        if side == "left":
            computed = hash_pair(sibling, computed)
        else:
            computed = hash_pair(computed, sibling)
    return computed == root
