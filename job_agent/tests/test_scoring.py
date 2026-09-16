"""Tests for Agent 2 - scoring, filtering, and ranking."""

import unittest
from datetime import date

from job_agent.config import SearchProfile
from job_agent.models import JobPosting
from job_agent.scoring import ScoringAgent


def _job(**kw):
    base = dict(title="BD Lead", company="Figure", url="u", description="", remote=False)
    base.update(kw)
    return JobPosting(**base)


class TestScoring(unittest.TestCase):
    def setUp(self):
        self.agent = ScoringAgent(SearchProfile())
        self.today = date(2026, 6, 15)

    def test_strong_match_scores_high(self):
        job = _job(
            title="Head of Business Development",
            description="Own partnerships and revenue for our crypto platform. "
                        "Go-to-market, licensing, strategic deals.",
            remote=True, salary_min=160_000, salary_max=200_000,
            posted_date=self.today,
        )
        scored = self.agent.score_one(job, today=self.today)
        self.assertGreaterEqual(scored.score, 8.0)
        self.assertTrue(scored.reasons)

    def test_off_target_scores_low(self):
        job = _job(
            title="Junior Marketing Coordinator",
            description="Social media for a retail brand.",
            salary_min=55_000, salary_max=65_000, posted_date=self.today,
        )
        scored = self.agent.score_one(job, today=self.today)
        self.assertLess(scored.score, 7.0)

    def test_components_are_explainable(self):
        job = _job(description="crypto partnerships", salary_min=150_000)
        scored = self.agent.score_one(job, today=self.today)
        self.assertIn("role_match", scored.components)
        self.assertIn("industry_match", scored.components)
        self.assertIn("salary", scored.components)

    def test_freshness_decays(self):
        fresh = _job(posted_date=self.today, salary_min=150_000, description="crypto bd")
        stale = _job(posted_date=date(2026, 5, 1), salary_min=150_000, description="crypto bd")
        self.assertGreater(
            self.agent.score_one(fresh, today=self.today).components["freshness"],
            self.agent.score_one(stale, today=self.today).components["freshness"],
        )


class TestRanking(unittest.TestCase):
    def test_filters_below_floor_and_caps_top_n(self):
        profile = SearchProfile(daily_top_n=2, min_score=6.0)
        agent = ScoringAgent(profile)
        jobs = [
            _job(title="BD Lead", description="crypto partnerships revenue",
                 salary_min=160_000, remote=True, posted_date=date(2026, 6, 15)),
            _job(title="Strategy Director", description="fintech operations strategy",
                 salary_min=150_000, remote=True, posted_date=date(2026, 6, 15)),
            _job(title="Partnerships", description="web3 bd growth",
                 salary_min=140_000, remote=True, posted_date=date(2026, 6, 15)),
            # below salary floor -> filtered regardless of score
            _job(title="BD Lead", company="Acme", url="u2",
                 description="crypto partnerships", salary_min=40_000, salary_max=60_000),
        ]
        ranked = agent.rank(jobs, today=date(2026, 6, 15))
        self.assertEqual(len(ranked), 2)
        self.assertGreaterEqual(ranked[0].score, ranked[1].score)
        self.assertTrue(all(s.job.salary_top >= 100_000 for s in ranked))

    def test_unknown_salary_is_not_rejected(self):
        agent = ScoringAgent(SearchProfile(min_score=0.0, daily_top_n=10))
        job = _job(description="crypto partnerships", posted_date=date(2026, 6, 15))
        ranked = agent.rank([job], today=date(2026, 6, 15))
        self.assertEqual(len(ranked), 1)


if __name__ == "__main__":
    unittest.main()
