"""Incident aggregation - turn an alert firehose into a short incident queue.

Analysts drown in alerts; they investigate *incidents*. This stage clusters the
unified alert feed into :class:`Incident` objects by shared actor and time
proximity, escalates incident severity to the worst contributing alert, and
infers a root-cause label from the mix of alert types (e.g. an access spike plus
a billing anomaly for one user reads as a likely compromised account, not two
unrelated events).

The goal is the design doc's "alerts -> incidents" shift: far fewer items, each
with its own trace lineage preserved, cutting analyst fatigue without losing a
single underlying signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from clearpulse.models import Alert, new_trace_id, utcnow

# Severity ordering for escalation (higher wins).
_SEVERITY_RANK = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

# Root-cause inference: a frozenset of alert types -> a human label. Checked by
# subset, so extra alert types in an incident still match the base pattern.
_ROOT_CAUSE_RULES: list[tuple[frozenset[str], str]] = [
    (frozenset({"SNOOPING_SUSPECT", "TEMPORAL_BILLING_ANOMALY"}),
     "likely_compromised_account"),
    (frozenset({"ACCESS_VOLUME_SPIKE", "TEMPORAL_BILLING_ANOMALY"}),
     "likely_compromised_account"),
    (frozenset({"TEMPORAL_BILLING_ANOMALY"}), "billing_fraud_pattern"),
    (frozenset({"SNOOPING_SUSPECT"}), "insider_snooping"),
    (frozenset({"UNENCRYPTED_PHI"}), "data_exposure"),
]


def _severity_max(a: str, b: str) -> str:
    return a if _SEVERITY_RANK.get(a, 0) >= _SEVERITY_RANK.get(b, 0) else b


@dataclass
class Incident:
    """A clustered group of related alerts presented as one investigation."""

    incident_id: str
    severity: str
    summary: str
    alert_ids: list[str] = field(default_factory=list)
    trace_ids: list[str] = field(default_factory=list)
    user_ids: list[str] = field(default_factory=list)
    alert_types: list[str] = field(default_factory=list)
    root_cause: str = "uncategorised"
    started_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    @property
    def alert_count(self) -> int:
        return len(self.alert_ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "severity": self.severity,
            "summary": self.summary,
            "root_cause": self.root_cause,
            "alert_count": self.alert_count,
            "alert_ids": list(self.alert_ids),
            "trace_ids": list(self.trace_ids),
            "user_ids": list(self.user_ids),
            "alert_types": sorted(set(self.alert_types)),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class IncidentAggregator:
    """Groups alerts into incidents by shared actor and time window."""

    def __init__(self, window: timedelta = timedelta(minutes=30)) -> None:
        self.window = window
        self._incidents: list[Incident] = []

    def _match(self, alert: Alert, now: datetime) -> Optional[Incident]:
        """Find an open incident this alert belongs to (same user, in-window).

        Falls back to the same trace lineage when the alert has no user (e.g. a
        compliance/PHI finding keyed by file path), so encounter-scoped alerts
        still coalesce.
        """
        for incident in reversed(self._incidents):
            if incident.last_seen is None:
                continue
            if now - incident.last_seen > self.window:
                continue
            if alert.user_id and alert.user_id in incident.user_ids:
                return incident
            if alert.trace_id and alert.trace_id in incident.trace_ids:
                return incident
        return None

    def _infer_root_cause(self, types: set[str]) -> str:
        for pattern, label in _ROOT_CAUSE_RULES:
            if pattern <= types:
                return label
        return "uncategorised"

    def ingest(self, alert: Alert) -> Incident:
        """Add one alert, returning the incident it landed in (new or existing)."""
        now = alert.created_at or utcnow()
        incident = self._match(alert, now)
        if incident is None:
            incident = Incident(
                incident_id=f"INC-{new_trace_id()[:8]}",
                severity=alert.severity,
                summary=alert.summary,
                started_at=now,
            )
            self._incidents.append(incident)

        incident.alert_ids.append(alert.alert_id)
        if alert.trace_id and alert.trace_id not in incident.trace_ids:
            incident.trace_ids.append(alert.trace_id)
        if alert.user_id and alert.user_id not in incident.user_ids:
            incident.user_ids.append(alert.user_id)
        incident.alert_types.append(alert.alert_type)
        incident.severity = _severity_max(incident.severity, alert.severity)
        incident.last_seen = now if incident.last_seen is None \
            else max(incident.last_seen, now)
        incident.root_cause = self._infer_root_cause(set(incident.alert_types))
        # Keep the summary anchored to the highest-severity contributing alert.
        if _SEVERITY_RANK.get(alert.severity, 0) >= _SEVERITY_RANK.get(incident.severity, 0):
            incident.summary = alert.summary
        return incident

    def aggregate(self, alerts: list[Alert]) -> list[Incident]:
        """Cluster a batch of alerts; returns incidents newest-first by start."""
        for alert in sorted(alerts, key=lambda a: a.created_at or utcnow()):
            self.ingest(alert)
        return self.incidents

    @property
    def incidents(self) -> list[Incident]:
        return sorted(self._incidents,
                      key=lambda i: i.started_at or utcnow(), reverse=True)

    def reduction_ratio(self, alert_total: int) -> float:
        """Fraction of items removed from the analyst queue (0..1)."""
        if alert_total <= 0:
            return 0.0
        return 1.0 - (len(self._incidents) / alert_total)
