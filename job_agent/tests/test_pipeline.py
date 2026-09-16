"""End-to-end test for the wired JobAutomationPipeline."""

import unittest
from datetime import date

from job_agent.config import SearchProfile
from job_agent.models import ApplicationStatus, JobPosting
from job_agent.pipeline import JobAutomationPipeline
from job_agent.sourcing import StaticSource


def _board():
    today = date(2026, 6, 15)
    return [
        JobPosting(title="Head of Business Development", company="Figure", url="u1",
                   description="partnerships and revenue for our crypto platform, gtm, licensing",
                   remote=True, salary_min=160_000, salary_max=200_000, posted_date=today,
                   contact_name="Dana"),
        JobPosting(title="Director of Strategy & Operations", company="Block", url="u2",
                   description="operations and strategy across fintech and bitcoin",
                   remote=True, salary_min=150_000, salary_max=190_000, posted_date=today),
        JobPosting(title="Junior Marketing Coordinator", company="Acme", url="u3",
                   description="social media for retail", salary_min=55_000, salary_max=65_000,
                   posted_date=today),
    ]


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = JobAutomationPipeline(
            profile=SearchProfile(),
            master_resume="closed $40M in crypto partnerships",
            sources=[StaticSource(_board())],
        )

    def test_run_daily_shortlists_and_personalises(self):
        staged = self.pipeline.run_daily(today=date(2026, 6, 15))
        # The off-target / low-salary role is filtered out.
        self.assertEqual(len(staged), 2)
        companies = {a.job.company for a in staged}
        self.assertEqual(companies, {"Figure", "Block"})
        # Every staged row carries a tailored kit.
        for app in staged:
            self.assertIsNotNone(app.kit)
            self.assertTrue(app.kit.outreach_message)
            self.assertEqual(app.status, ApplicationStatus.QUEUED)

    def test_full_flow_through_followup_and_intelligence(self):
        staged = self.pipeline.run_daily(today=date(2026, 6, 15))
        top = staged[0]
        self.pipeline.tracking.mark_applied(top.id, on=date(2026, 6, 10))
        due = self.pipeline.follow_ups_due(today=date(2026, 6, 15))
        self.assertEqual(len(due), 1)
        self.assertIn(top.job.company, due[0]["message"])

        self.pipeline.tracking.set_status(top.id, ApplicationStatus.INTERVIEW)
        report = self.pipeline.intelligence_report()
        self.assertEqual(report["total_responded"], 1)


if __name__ == "__main__":
    unittest.main()
