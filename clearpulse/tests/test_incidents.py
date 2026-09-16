"""Tests for the ClearPulse incident aggregation layer.

    python3 -m unittest clearpulse.tests.test_incidents -v
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from clearpulse.incidents.aggregator import IncidentAggregator
from clearpulse.models import Alert

UTC = timezone.utc


def _alert(alert_type, severity, user_id, when, summary="x", trace_id=None):
    return Alert(alert_type=alert_type, severity=severity, summary=summary,
                 user_id=user_id, trace_id=trace_id, created_at=when)


class IncidentAggregatorTests(unittest.TestCase):
    def test_same_user_in_window_collapses_to_one_incident(self):
        agg = IncidentAggregator(window=timedelta(minutes=30))
        t0 = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
        agg.ingest(_alert("SNOOPING_SUSPECT", "HIGH", "NURSE-7", t0))
        agg.ingest(_alert("TEMPORAL_BILLING_ANOMALY", "CRITICAL", "NURSE-7",
                          t0 + timedelta(minutes=5)))
        self.assertEqual(len(agg.incidents), 1)
        inc = agg.incidents[0]
        self.assertEqual(inc.alert_count, 2)
        # Severity escalates to the worst contributor.
        self.assertEqual(inc.severity, "CRITICAL")
        # Access spike + billing anomaly for one user => compromised account.
        self.assertEqual(inc.root_cause, "likely_compromised_account")

    def test_same_user_outside_window_splits(self):
        agg = IncidentAggregator(window=timedelta(minutes=30))
        t0 = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
        agg.ingest(_alert("SNOOPING_SUSPECT", "HIGH", "NURSE-7", t0))
        agg.ingest(_alert("SNOOPING_SUSPECT", "HIGH", "NURSE-7",
                          t0 + timedelta(hours=2)))
        self.assertEqual(len(agg.incidents), 2)

    def test_different_users_are_distinct_incidents(self):
        agg = IncidentAggregator()
        t0 = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
        agg.ingest(_alert("SNOOPING_SUSPECT", "HIGH", "U1", t0))
        agg.ingest(_alert("SNOOPING_SUSPECT", "HIGH", "U2", t0))
        self.assertEqual(len(agg.incidents), 2)

    def test_userless_alerts_coalesce_on_trace(self):
        agg = IncidentAggregator()
        t0 = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
        agg.ingest(_alert("UNENCRYPTED_PHI", "MEDIUM", None, t0, trace_id="phi:f"))
        agg.ingest(_alert("UNENCRYPTED_PHI", "HIGH", None,
                          t0 + timedelta(minutes=1), trace_id="phi:f"))
        self.assertEqual(len(agg.incidents), 1)
        self.assertEqual(agg.incidents[0].root_cause, "data_exposure")

    def test_reduction_ratio(self):
        agg = IncidentAggregator()
        t0 = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
        alerts = [_alert("SNOOPING_SUSPECT", "HIGH", "U1",
                         t0 + timedelta(minutes=i)) for i in range(10)]
        agg.aggregate(alerts)
        self.assertEqual(len(agg.incidents), 1)
        self.assertAlmostEqual(agg.reduction_ratio(10), 0.9)


if __name__ == "__main__":
    unittest.main(verbosity=2)
