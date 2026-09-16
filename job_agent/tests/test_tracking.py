"""Tests for Agent 4 - tracking, follow-up scheduling, and the intelligence layer."""

import unittest
from datetime import date

from job_agent.config import SearchProfile
from job_agent.intelligence import IntelligenceLayer
from job_agent.models import ApplicationStatus, JobPosting, ScoredJob
from job_agent.tracking import TrackingAgent


def _scored(company="Figure", title="BD Lead", salary=160_000):
    job = JobPosting(title=title, company=company, url="u",
                     salary_min=salary, salary_max=salary, contact_name="Dana")
    return ScoredJob(job=job, score=9.0, reasons=["strong fit in crypto bd"])


class TestTracking(unittest.TestCase):
    def setUp(self):
        self.agent = TrackingAgent(SearchProfile(follow_up_days=4))

    def test_stage_then_apply_arms_follow_up(self):
        app = self.agent.stage(_scored())
        self.assertEqual(app.status, ApplicationStatus.QUEUED)
        self.agent.mark_applied(app.id, on=date(2026, 6, 10))
        self.assertEqual(app.status, ApplicationStatus.APPLIED)
        self.assertEqual(app.follow_up_date, date(2026, 6, 14))

    def test_due_for_follow_up(self):
        app = self.agent.stage(_scored())
        self.agent.mark_applied(app.id, on=date(2026, 6, 10))
        due = self.agent.due_for_follow_up(today=date(2026, 6, 15))
        self.assertEqual(len(due), 1)
        # Not yet due the day after applying.
        self.assertEqual(self.agent.due_for_follow_up(today=date(2026, 6, 11)), [])

    def test_follow_up_message_uses_contact_and_anchor(self):
        app = self.agent.stage(_scored())
        msg = self.agent.follow_up_message(app)
        self.assertIn("Dana", msg)
        self.assertIn("Figure", msg)

    def test_record_follow_up_rearms_clock(self):
        app = self.agent.stage(_scored())
        self.agent.mark_applied(app.id, on=date(2026, 6, 10))
        self.agent.record_follow_up(app.id, on=date(2026, 6, 14))
        self.assertEqual(app.status, ApplicationStatus.FOLLOWED_UP)
        self.assertEqual(app.follow_up_date, date(2026, 6, 18))


class TestIntelligence(unittest.TestCase):
    def test_conversion_by_function_and_band(self):
        agent = TrackingAgent(SearchProfile())
        a = agent.stage(_scored(company="Figure", title="Business Development Lead"))
        agent.mark_applied(a.id, on=date(2026, 6, 1))
        agent.set_status(a.id, ApplicationStatus.INTERVIEW)

        b = agent.stage(_scored(company="Acme", title="Operations Manager", salary=120_000))
        agent.mark_applied(b.id, on=date(2026, 6, 2))
        agent.set_status(b.id, ApplicationStatus.REJECTED)

        report = IntelligenceLayer().analyze(agent.applications)
        self.assertEqual(report["total_applied"], 2)
        self.assertEqual(report["total_responded"], 1)
        self.assertIn("business development", report["by_function"])
        self.assertEqual(report["by_function"]["business development"]["response_rate"], 1.0)
        self.assertIn("Figure", report["fastest_responding_companies"])
        self.assertTrue(report["recommendations"])

    def test_handles_empty_tracker(self):
        report = IntelligenceLayer().analyze([])
        self.assertEqual(report["total_applied"], 0)
        self.assertTrue(report["recommendations"])


if __name__ == "__main__":
    unittest.main()
