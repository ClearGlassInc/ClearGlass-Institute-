"""Core ClearPulse data structures shared across every pipeline stage.

These are intentionally plain :mod:`dataclasses` (no third-party dependency) so
the logic layer can be unit-tested without FastAPI, pydantic, Redis, or any
external runtime. The FastAPI gateway in :mod:`clearpulse.backend` adapts these
to pydantic request/response models at its edge.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Trace identity
# ---------------------------------------------------------------------------

def new_trace_id() -> str:
    """Return a time-ordered ClearPulse Trace ID (UUIDv7-style).

    Python 3.11 has no ``uuid.uuid7`` helper, so we build a draft-RFC-9562
    compatible value: a 48-bit millisecond timestamp prefix followed by random
    bits with the version (7) and variant fields set. The time prefix keeps IDs
    broadly ordered by creation millisecond (ids minted in the same millisecond
    are not mutually ordered), which is what the immutable ledger relies on.
    """
    unix_ms = time.time_ns() // 1_000_000
    rand = int.from_bytes(os.urandom(10), "big")  # 80 random bits
    rand_a = (rand >> 62) & 0x0FFF                 # 12 bits
    rand_b = rand & 0x3FFFFFFFFFFFFFFF             # 62 bits
    # 48 bits time | 4 bits version | 12 bits randA | 2 bits variant | 62 bits randB
    value = (unix_ms & 0xFFFFFFFFFFFF) << 80
    value |= 0x7 << 76          # version 7
    value |= rand_a << 64
    value |= 0b10 << 62         # RFC 4122 variant
    value |= rand_b
    return str(uuid.UUID(int=value & ((1 << 128) - 1)))


def utcnow() -> datetime:
    """Timezone-aware UTC now (encounters are correlated in UTC end to end)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Layer 1/2 - observable facts emitted by the ingestion parser
# ---------------------------------------------------------------------------

@dataclass
class ObservableFact:
    """One atomic encounter-procedure pair extracted from a FHIR bundle.

    Mirrors the flat JSON event placed on ``stream:tx:new`` in the design doc.
    """

    trace_id: str
    event_type: str
    patient_id: str
    provider_id: str
    cpt_code: str
    service_start: datetime
    service_end: datetime
    dept: str
    diagnosis_codes: list[str] = field(default_factory=list)
    vip: bool = False

    @property
    def duration_seconds(self) -> float:
        return max(0.0, (self.service_end - self.service_start).total_seconds())

    def to_event(self) -> dict[str, Any]:
        """Serialise to the flat stream event shape (timestamps as ISO-8601)."""
        return {
            "trace_id": self.trace_id,
            "event_type": self.event_type,
            "patient_id": self.patient_id,
            "provider_id": self.provider_id,
            "cpt_code": self.cpt_code,
            "service_start": self.service_start.isoformat(),
            "service_end": self.service_end.isoformat(),
            "dept": self.dept,
            "diagnosis_codes": list(self.diagnosis_codes),
            "vip": self.vip,
        }


@dataclass
class AccessEvent:
    """A single staff record-access entry parsed from the ADT/access log."""

    trace_id: str
    user_id: str
    patient_id: str
    dept: str
    timestamp: datetime
    action: str = "record_open"


# ---------------------------------------------------------------------------
# Layer 2 - risk output
# ---------------------------------------------------------------------------

@dataclass
class RiskEnvelope:
    """Explainable scoring result published to ``stream:tx:scored``.

    ``components`` is the per-factor point breakdown and ``triggering_facts``
    captures the human-readable reasons, so any score can be unpacked.
    """

    trace_id: str
    score: int
    level: str
    components: dict[str, int]
    triggering_facts: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "score": self.score,
            "level": self.level,
            "components": dict(self.components),
            "triggering_facts": list(self.triggering_facts),
            "created_at": self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Layers 3/4/5 - alerts and compliance findings
# ---------------------------------------------------------------------------

@dataclass
class Alert:
    """A normalised event on the unified ``stream:alerts`` channel."""

    alert_type: str
    severity: str
    summary: str
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)
    alert_id: str = field(default_factory=lambda: new_trace_id())
    created_at: datetime = field(default_factory=utcnow)

    def dedup_key(self) -> tuple[Optional[str], str]:
        """Alerts collapse on (trace_id, alert_type) within the dedup window."""
        return (self.trace_id, self.alert_type)


@dataclass
class ComplianceFinding:
    """An at-rest PHI/PII match discovered by the compliance auto-scan."""

    file_path: str
    pattern_name: str
    masked_snippet: str
    line_no: int
    detected_at: datetime = field(default_factory=utcnow)
