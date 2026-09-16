"""End-to-end ClearPulse pipeline wiring (single-process reference path).

This binds the stages described in the design doc - ingestion -> windowed
correlation -> risk scoring -> unified alerting - into one object so the FastAPI
gateway and the demo share identical behaviour. In a distributed deployment each
stage runs as its own service communicating over Redis/PostgreSQL; the seams
here (``window``, ``risk``, ``access``, ``router``) are the swap points.
"""

from __future__ import annotations

from typing import Any, Optional

from clearpulse.alerts.router import AlertRouter
from clearpulse.audit.ledger import AuditChain
from clearpulse.compliance.scanner import PHIScanner, severity_from_findings
from clearpulse.engine.access import AccessSpikeDetector
from clearpulse.engine.risk import RiskScorer
from clearpulse.engine.window import SlidingWindowState
from clearpulse.incidents.aggregator import IncidentAggregator
from clearpulse.ingestion.parser import parse_access_log_entry, parse_encounter_bundle
from clearpulse.models import Alert, RiskEnvelope

# Risk score at/above which an alert is raised (matches rules' high threshold).
_HIGH_THRESHOLD = 70


class ClearPulsePipeline:
    """Reference orchestration that scores encounters and raises alerts."""

    def __init__(
        self,
        scorer: Optional[RiskScorer] = None,
        window: Optional[SlidingWindowState] = None,
        access: Optional[AccessSpikeDetector] = None,
        router: Optional[AlertRouter] = None,
        scanner: Optional[PHIScanner] = None,
        audit: Optional[AuditChain] = None,
        incidents: Optional[IncidentAggregator] = None,
    ) -> None:
        self.scorer = scorer or RiskScorer()
        self.window = window or SlidingWindowState()
        self.access = access or AccessSpikeDetector()
        self.router = router or AlertRouter()
        self.scanner = scanner or PHIScanner()
        # Forensic + investigation layers: every accepted alert is sealed into
        # the tamper-evident audit chain and clustered into an incident.
        self.audit = audit or AuditChain()
        self.incidents = incidents or IncidentAggregator()
        self.high_threshold = self.scorer.rules["thresholds"]["high_min"]
        # Users currently flagged as snooping, so we alert once per spike
        # episode rather than on every access event over threshold.
        self._suspect_users: set[str] = set()

    def _record(self, alert: Optional[Alert]) -> Optional[Alert]:
        """Seal an accepted alert into the audit chain and the incident queue.

        ``None`` (a deduplicated alert) passes through untouched, so the forensic
        ledger records exactly what the unified feed accepted - no more, no less.
        """
        if alert is not None:
            self.audit.append(
                "ALERT", alert.payload or {"summary": alert.summary},
                trace_id=alert.trace_id)
            self.incidents.ingest(alert)
        return alert

    def process_encounter(self, bundle: dict[str, Any]) -> list[RiskEnvelope]:
        """Ingest a bundle, correlate against the window, score, and alert."""
        facts = parse_encounter_bundle(bundle)
        envelopes: list[RiskEnvelope] = []
        for fact in facts:
            self.window.prune(now=fact.service_start)
            overlaps = self.window.overlapping(fact)
            self.window.add(fact)
            envelope = self.scorer.score(fact, overlaps)
            envelopes.append(envelope)
            # A confirmed temporal billing overlap is alert-worthy on its own;
            # severity escalates to CRITICAL once the total crosses the high band.
            if "temporal_billing_overlap" in envelope.components:
                severity = ("CRITICAL" if envelope.score >= self.high_threshold
                            else "HIGH")
                self._record(self.router.submit(Alert(
                    alert_type="TEMPORAL_BILLING_ANOMALY",
                    severity=severity,
                    summary=(f"Billing collision for {fact.patient_id}: "
                             f"{fact.cpt_code} overlaps a concurrent claim"),
                    trace_id=fact.trace_id,
                    user_id=fact.provider_id,
                    payload=envelope.to_dict(),
                )))
        return envelopes

    def process_access(
        self,
        entry: dict[str, Any],
        *,
        baseline_median: float,
        baseline_std: float,
    ) -> dict[str, Any]:
        """Record a staff access event and raise a snooping alert if anomalous."""
        event = parse_access_log_entry(entry)
        self.access.record(event.user_id, event.patient_id, event.timestamp)
        verdict = self.access.evaluate(
            event.user_id, event.timestamp, baseline_median, baseline_std,
        )
        if verdict["is_suspect"]:
            if event.user_id not in self._suspect_users:
                self._suspect_users.add(event.user_id)
                self._record(self.router.submit(Alert(
                    alert_type="SNOOPING_SUSPECT",
                    severity="HIGH",
                    summary=(f"User {event.user_id} accessed {verdict['count']} "
                             f"records (z={verdict['zscore']:.1f})"),
                    trace_id=event.trace_id,
                    user_id=event.user_id,
                    payload=dict(verdict),
                )))
        else:
            # Activity returned to baseline; a future spike can re-alert.
            self._suspect_users.discard(event.user_id)
        return verdict

    def scan_paths(self, paths: list[str]) -> list[Alert]:
        """Run the at-rest PHI scan over paths and raise compliance alerts."""
        findings = self.scanner.scan_paths(paths)
        by_file: dict[str, int] = {}
        for finding in findings:
            by_file[finding.file_path] = by_file.get(finding.file_path, 0) + 1
        raised: list[Alert] = []
        for file_path, count in by_file.items():
            alert = self._record(self.router.submit(Alert(
                alert_type="UNENCRYPTED_PHI",
                severity=severity_from_findings(count),
                summary=f"{count} unencrypted identifier(s) found in {file_path}",
                # Per-file dedup identity: distinct files stay distinct, while a
                # re-scan of the same file within the window still collapses.
                trace_id=f"phi:{file_path}",
                payload={"file_path": file_path, "match_count": count},
            )))
            if alert is not None:
                raised.append(alert)
        return raised
