"""Stdlib unittest suite for the ClearPulse core engine.

Runs without third-party dependencies:

    python3 -m unittest clearpulse.tests.test_clearpulse -v
"""

from __future__ import annotations

import os
import tempfile
import time
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from clearpulse.alerts.router import AlertRouter
from clearpulse.compliance.scanner import (
    PHIScanner,
    mask_snippet,
    severity_from_findings,
)
from clearpulse.engine.access import AccessSpikeDetector
from clearpulse.engine.risk import RiskScorer, overlap_ratio
from clearpulse.engine.window import SlidingWindowState
from clearpulse.ingestion.parser import parse_encounter_bundle
from clearpulse.models import Alert, ObservableFact, new_trace_id

UTC = timezone.utc


def _fact(start: str, end: str, **kw) -> ObservableFact:
    base = dict(
        trace_id=new_trace_id(),
        event_type="procedure_claim",
        patient_id="P-9912",
        provider_id="DR-442",
        cpt_code="73721",
        service_start=datetime.fromisoformat(start).replace(tzinfo=UTC),
        service_end=datetime.fromisoformat(end).replace(tzinfo=UTC),
        dept="RADIOLOGY",
    )
    base.update(kw)
    return ObservableFact(**base)


class TraceIdTests(unittest.TestCase):
    def test_trace_id_is_valid_uuid_v7(self):
        tid = new_trace_id()
        parsed = uuid.UUID(tid)
        self.assertEqual(parsed.version, 7)
        self.assertEqual(parsed.variant, uuid.RFC_4122)

    def test_trace_ids_are_time_ordered_across_ms(self):
        # UUIDv7 orders by its 48-bit millisecond prefix; ids minted in the same
        # millisecond carry random low bits, so we only assert the time prefix
        # is non-decreasing as wall-clock advances.
        prefixes = []
        for _ in range(3):
            prefixes.append(uuid.UUID(new_trace_id()).int >> 80)
            time.sleep(0.002)
        self.assertEqual(prefixes, sorted(prefixes))


class OverlapTests(unittest.TestCase):
    def test_full_overlap_ratio(self):
        mri = _fact("2026-06-01T09:00:00", "2026-06-01T09:45:00")
        consult = _fact("2026-06-01T09:10:00", "2026-06-01T09:25:00",
                        provider_id="DR-999", cpt_code="99213")
        # 15-min consult sits entirely inside the 45-min MRI -> ratio 1.0
        self.assertAlmostEqual(overlap_ratio(mri, consult), 1.0)

    def test_partial_overlap_ratio(self):
        a = _fact("2026-06-01T09:00:00", "2026-06-01T09:20:00")  # 20 min
        b = _fact("2026-06-01T09:10:00", "2026-06-01T09:30:00",
                  cpt_code="99213")                               # 20 min
        # intersection 09:10-09:20 = 10 min over min duration 20 min = 0.5
        self.assertAlmostEqual(overlap_ratio(a, b), 0.5)

    def test_no_overlap_is_zero(self):
        a = _fact("2026-06-01T09:00:00", "2026-06-01T09:15:00")
        b = _fact("2026-06-01T10:00:00", "2026-06-01T10:15:00", cpt_code="99213")
        self.assertEqual(overlap_ratio(a, b), 0.0)


class RiskScorerTests(unittest.TestCase):
    def setUp(self):
        self.scorer = RiskScorer()

    def test_overlap_awards_forty_points(self):
        mri = _fact("2026-06-01T09:00:00", "2026-06-01T09:45:00")
        consult = _fact("2026-06-01T09:10:00", "2026-06-01T09:25:00",
                        provider_id="DR-999", cpt_code="99213")
        env = self.scorer.score(mri, [consult])
        self.assertEqual(env.components.get("temporal_billing_overlap"), 40)
        self.assertEqual(env.score, 40)
        self.assertEqual(env.level, "medium")

    def test_combined_signals_cross_high_threshold(self):
        # Overlap (40) + full access spike (50) -> capped at 100 -> "high".
        mri = _fact("2026-06-01T09:00:00", "2026-06-01T09:45:00", vip=False)
        consult = _fact("2026-06-01T09:10:00", "2026-06-01T09:25:00",
                        provider_id="DR-999", cpt_code="99213")
        env = self.scorer.score(mri, [consult], access_zscore=6.0)
        self.assertGreaterEqual(env.score, 70)
        self.assertEqual(env.level, "high")
        self.assertLessEqual(env.score, 100)

    def test_off_hours_flag(self):
        night = _fact("2026-06-01T02:00:00", "2026-06-01T02:30:00")
        env = self.scorer.score(night, [])
        self.assertEqual(env.components.get("off_hours_activity"), 10)

    def test_low_risk_when_no_signals(self):
        day = _fact("2026-06-01T09:00:00", "2026-06-01T09:30:00")
        env = self.scorer.score(day, [])
        self.assertEqual(env.score, 0)
        self.assertEqual(env.level, "low")


class WindowTests(unittest.TestCase):
    def test_overlapping_returns_concurrent_claim(self):
        window = SlidingWindowState(timedelta(minutes=15))
        mri = _fact("2026-06-01T09:00:00", "2026-06-01T09:45:00")
        window.add(mri)
        consult = _fact("2026-06-01T09:10:00", "2026-06-01T09:25:00",
                        provider_id="DR-999", cpt_code="99213")
        self.assertEqual(window.overlapping(consult), [mri])

    def test_prune_drops_stale_facts(self):
        window = SlidingWindowState(timedelta(minutes=15))
        window.add(_fact("2026-06-01T08:00:00", "2026-06-01T08:15:00"))
        window.prune(now=datetime(2026, 6, 1, 9, 0, tzinfo=UTC))
        self.assertEqual(window.active_count(), 0)


class AccessSpikeTests(unittest.TestCase):
    def test_zscore_and_suspect_flag(self):
        det = AccessSpikeDetector(window=timedelta(hours=1), suspect_zscore=3.0)
        now = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
        for i in range(50):
            det.record("nurse-7", f"P-{i}", now)
        verdict = det.evaluate("nurse-7", now, baseline_median=8, baseline_std=4)
        self.assertEqual(verdict["count"], 50)
        self.assertTrue(verdict["is_suspect"])
        self.assertGreater(verdict["zscore"], 3.0)

    def test_zero_std_is_safe(self):
        self.assertEqual(AccessSpikeDetector.zscore(50, 8, 0), 0.0)


class ScannerTests(unittest.TestCase):
    def test_masking_hides_most_characters(self):
        self.assertEqual(mask_snippet("123-45-6789"), "*********89")

    def test_detects_ssn_and_masks_it(self):
        scanner = PHIScanner()
        findings = scanner.scan_text("patient ssn 123-45-6789 on file")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].pattern_name, "ssn")
        self.assertNotIn("123-45-6789", findings[0].masked_snippet)

    def test_severity_tiers(self):
        self.assertEqual(severity_from_findings(200), "CRITICAL")
        self.assertEqual(severity_from_findings(10), "HIGH")
        self.assertEqual(severity_from_findings(1), "MEDIUM")
        self.assertEqual(severity_from_findings(0), "INFO")

    def test_scan_file_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "export.csv")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("name,ssn\nJane Doe,111-22-3333\n")
            findings = PHIScanner().scan_file(path)
        self.assertTrue(any(f.pattern_name == "ssn" for f in findings))


class AlertRouterTests(unittest.TestCase):
    def _alert(self, **kw):
        base = dict(alert_type="TEMPORAL_BILLING_ANOMALY", severity="CRITICAL",
                    summary="x", trace_id="t-1")
        base.update(kw)
        return Alert(**base)

    def test_dedup_suppresses_repeat(self):
        router = AlertRouter()
        first = router.submit(self._alert())
        second = router.submit(self._alert())
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(len(router.accepted), 1)

    def test_correlation_links_access_and_billing(self):
        router = AlertRouter()
        router.submit(self._alert(alert_type="TEMPORAL_BILLING_ANOMALY",
                                  user_id="DR-442", trace_id="t-1"))
        router.submit(self._alert(alert_type="SNOOPING_SUSPECT", severity="HIGH",
                                  user_id="DR-442", trace_id="t-2"))
        self.assertEqual(len(router.correlations), 1)
        self.assertEqual(router.correlations[0]["hypothesis"],
                         "possible_compromised_account")


class IngestionTests(unittest.TestCase):
    def test_parse_simplified_bundle(self):
        bundle = {
            "patient_id": "P-9912", "provider_id": "DR-442", "dept": "RADIOLOGY",
            "procedures": [{
                "cpt_code": "73721",
                "service_start": "2026-06-01T09:00:00Z",
                "service_end": "2026-06-01T09:45:00Z",
                "diagnosis_codes": ["M25.561"],
            }],
        }
        facts = parse_encounter_bundle(bundle)
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].patient_id, "P-9912")
        self.assertEqual(facts[0].duration_seconds, 45 * 60)
        # Trailing 'Z' parsed as UTC.
        self.assertEqual(facts[0].service_start.tzinfo, UTC)

    def test_parse_raw_fhir_procedure_bundle(self):
        # Procedure.performer is a LIST of components wrapping actor.reference.
        bundle = {
            "resourceType": "Bundle",
            "entry": [{"resource": {
                "resourceType": "Procedure",
                "subject": {"reference": "Patient/P-9912"},
                "performer": [{"actor": {"reference": "Practitioner/DR-442"}}],
                "code": {"coding": [{"code": "73721"}]},
                "performedPeriod": {"start": "2026-06-01T09:00:00Z",
                                    "end": "2026-06-01T09:45:00Z"},
            }}],
        }
        facts = parse_encounter_bundle(bundle)
        self.assertEqual(facts[0].patient_id, "P-9912")
        self.assertEqual(facts[0].provider_id, "DR-442")
        self.assertEqual(facts[0].cpt_code, "73721")


class PipelineTests(unittest.TestCase):
    def test_billing_collision_raises_alert(self):
        from clearpulse.pipeline import ClearPulsePipeline

        pipeline = ClearPulsePipeline()
        mri = {
            "patient_id": "P-9912", "provider_id": "DR-442", "dept": "RADIOLOGY",
            "procedures": [{"cpt_code": "73721",
                            "service_start": "2026-06-01T09:00:00Z",
                            "service_end": "2026-06-01T09:45:00Z"}],
        }
        consult = {
            "patient_id": "P-9912", "provider_id": "DR-999", "dept": "CARDIOLOGY",
            "procedures": [{"cpt_code": "99213",
                            "service_start": "2026-06-01T09:10:00Z",
                            "service_end": "2026-06-01T09:25:00Z"}],
        }
        self.assertEqual(pipeline.process_encounter(mri)[0].level, "low")
        envelopes = pipeline.process_encounter(consult)
        self.assertIn("temporal_billing_overlap", envelopes[0].components)
        types = [a.alert_type for a in pipeline.router.accepted]
        self.assertIn("TEMPORAL_BILLING_ANOMALY", types)

    def test_compliance_scan_raises_phi_alert(self):
        from clearpulse.pipeline import ClearPulsePipeline

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "discharge.csv")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("mrn,ssn\nMRN 1234567,123-45-6789\n")
            alerts = ClearPulsePipeline().scan_paths([tmp])
        self.assertTrue(alerts)
        self.assertEqual(alerts[0].alert_type, "UNENCRYPTED_PHI")

    def test_scan_multiple_files_are_not_deduped(self):
        from clearpulse.pipeline import ClearPulsePipeline

        with tempfile.TemporaryDirectory() as tmp:
            for name in ("a.csv", "b.csv"):
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                    fh.write("ssn\n123-45-6789\n")
            alerts = ClearPulsePipeline().scan_paths([tmp])
        # Distinct files must each yield their own alert (per-file dedup key).
        self.assertEqual(len({a.payload["file_path"] for a in alerts}), 2)


if __name__ == "__main__":
    unittest.main()
