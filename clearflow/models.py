"""Core ClearFlow data structures shared across the workflow engine.

These are intentionally plain :mod:`dataclasses` + :mod:`enum` (no third-party
dependency) so the orchestration logic can be unit-tested without FastAPI,
pydantic, a scheduler daemon, or any external runtime. The optional FastAPI
gateway in :mod:`clearflow.backend` adapts these at its edge.

The vocabulary is the daily operating model of ClearGlassInc: a *Strategic
Priority Matrix* of :class:`WorkItem` rows, grouped by :class:`Domain`, each
carrying a :class:`Priority`, a :class:`TimeBlock`, and a success metric. The
engine's contract is that exactly one keystone outcome (the single P0) is the
focus of the day, and every other domain stays gated until it lands.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, time as dtime, timezone
from enum import IntEnum, Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Trace identity
# ---------------------------------------------------------------------------

def new_trace_id() -> str:
    """Return a time-ordered ClearFlow Trace ID (UUIDv7-style).

    Mirrors the sibling ``clearpulse`` minting helper so a work item, pledge, or
    routed intel signal can always be traced by creation millisecond. Python
    3.11 ships no ``uuid.uuid7``; we build a draft-RFC-9562 compatible value:
    a 48-bit millisecond prefix, then random bits with version (7) and variant
    set.
    """
    unix_ms = time.time_ns() // 1_000_000
    rand = int.from_bytes(os.urandom(10), "big")  # 80 random bits
    rand_a = (rand >> 62) & 0x0FFF                 # 12 bits
    rand_b = rand & 0x3FFFFFFFFFFFFFFF             # 62 bits
    value = (unix_ms & 0xFFFFFFFFFFFF) << 80
    value |= 0x7 << 76          # version 7
    value |= rand_a << 64
    value |= 0b10 << 62         # RFC 4122 variant
    value |= rand_b
    return str(uuid.UUID(int=value & ((1 << 128) - 1)))


def utcnow() -> datetime:
    """Timezone-aware UTC now (the ledger orders events in UTC end to end)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class Priority(IntEnum):
    """Execution rank. Lower value == executed first (P0 is the keystone).

    Modelled as :class:`IntEnum` so items sort naturally by ``priority`` and the
    single most important row is simply ``min(items, key=...)``.
    """

    P0 = 0
    P1 = 1
    P2 = 2
    P3 = 3

    @property
    def label(self) -> str:
        return self.name

    @classmethod
    def parse(cls, raw: Any) -> "Priority":
        """Coerce ``"P0"`` / ``0`` / ``Priority.P0`` into a :class:`Priority`."""
        if isinstance(raw, Priority):
            return raw
        if isinstance(raw, int):
            return cls(raw)
        text = str(raw).strip().upper().lstrip("P")
        return cls(int(text))


class Status(str, Enum):
    """Lifecycle of a single work item.

    ``LOCKED`` is distinct from ``PENDING``: a locked item cannot be started yet
    because the day's keystone outcome has not landed. The gatekeeper flips
    ``LOCKED`` -> ``PENDING`` once the gate opens.
    """

    LOCKED = "LOCKED"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    BLOCKED = "BLOCKED"

    @property
    def is_terminal(self) -> bool:
        return self in (Status.DONE,)

    @property
    def is_startable(self) -> bool:
        return self in (Status.PENDING, Status.IN_PROGRESS)


# ---------------------------------------------------------------------------
# Time blocks
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TimeBlock:
    """A wall-clock window for a work item, e.g. ``08:00``–``10:00``.

    Times are naive local clock times (the operator works in one timezone); only
    the hour/minute matter for "is now inside this block?" scheduling.
    """

    start: dtime
    end: dtime

    @classmethod
    def parse(cls, text: str) -> "TimeBlock":
        """Parse ``"8-10 AM"`` / ``"10:30-11:30 AM"`` / ``"2-2:30 PM"``.

        A single meridiem (``AM``/``PM``) at the end applies to both ends unless
        an explicit one is attached to the start. ``12`` is handled correctly
        (12 AM -> 00:00, 12 PM -> 12:00).
        """
        raw = text.strip()
        trailing = ""
        upper = raw.upper()
        for token in ("AM", "PM"):
            if upper.endswith(token):
                trailing = token
                raw = raw[: -len(token)].strip()
                break
        left, _, right = raw.partition("-")
        start = cls._parse_clock(left.strip(), trailing)
        end = cls._parse_clock(right.strip(), trailing)
        return cls(start=start, end=end)

    @staticmethod
    def _parse_clock(token: str, default_meridiem: str) -> dtime:
        meridiem = default_meridiem
        upper = token.upper()
        for tok in ("AM", "PM"):
            if upper.endswith(tok):
                meridiem = tok
                token = token[: -len(tok)].strip()
                break
        hour_str, _, minute_str = token.partition(":")
        hour = int(hour_str)
        minute = int(minute_str) if minute_str else 0
        if meridiem == "PM" and hour != 12:
            hour += 12
        elif meridiem == "AM" and hour == 12:
            hour = 0
        return dtime(hour=hour, minute=minute)

    def contains(self, moment: dtime) -> bool:
        """True if ``moment`` falls in ``[start, end)`` (handles same-day only)."""
        return self.start <= moment < self.end

    def __str__(self) -> str:
        return f"{self.start.strftime('%H:%M')}-{self.end.strftime('%H:%M')}"


# ---------------------------------------------------------------------------
# Work items - the rows of the Strategic Priority Matrix
# ---------------------------------------------------------------------------

@dataclass
class WorkItem:
    """One row of the Strategic Priority Matrix.

    ``depends_on`` holds the trace ids of items that must reach ``DONE`` before
    this one can leave ``LOCKED``. The gating model wires every non-keystone
    item to depend (directly or transitively) on the keystone outcome.
    """

    domain: str
    action: str
    priority: Priority
    success_metric: str
    time_block: Optional[TimeBlock] = None
    effort_minutes: int = 60
    status: Status = Status.PENDING
    depends_on: list[str] = field(default_factory=list)
    evidence: Optional[str] = None
    trace_id: str = field(default_factory=new_trace_id)
    created_at: datetime = field(default_factory=utcnow)
    completed_at: Optional[datetime] = None

    @property
    def is_keystone(self) -> bool:
        return self.priority == Priority.P0

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "domain": self.domain,
            "action": self.action,
            "priority": self.priority.label,
            "success_metric": self.success_metric,
            "time_block": str(self.time_block) if self.time_block else None,
            "effort_minutes": self.effort_minutes,
            "status": self.status.value,
            "depends_on": list(self.depends_on),
            "evidence": self.evidence,
            "completed_at": (self.completed_at.isoformat()
                             if self.completed_at else None),
        }


# ---------------------------------------------------------------------------
# Pledges - the daily commitment ledger
# ---------------------------------------------------------------------------

class PledgeOutcome(str, Enum):
    OPEN = "OPEN"
    KEPT = "KEPT"
    MISSED = "MISSED"
    PARTIAL = "PARTIAL"


@dataclass
class Pledge:
    """A single daily commitment, reviewable the next day against evidence."""

    text: str
    outcome: PledgeOutcome = PledgeOutcome.OPEN
    note: Optional[str] = None
    trace_id: str = field(default_factory=new_trace_id)
    created_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "text": self.text,
            "outcome": self.outcome.value,
            "note": self.note,
        }


# ---------------------------------------------------------------------------
# Intelligence signals - the Critical Intelligence Brief
# ---------------------------------------------------------------------------

@dataclass
class IntelSignal:
    """One headline from the Critical Intelligence Brief.

    ``routed_to`` is filled in by :mod:`clearflow.intel.brief` once the signal is
    matched to a domain, so a workflow can attach the relevant signals to the
    item they inform.
    """

    headline: str
    routed_to: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    trace_id: str = field(default_factory=new_trace_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "headline": self.headline,
            "routed_to": self.routed_to,
            "keywords": list(self.keywords),
        }
