"""Tests for Agent 1 - sourcing, salary parsing, and dedup."""

import unittest
from datetime import date

from job_agent.models import JobPosting
from job_agent.sourcing import (
    SourcingAgent, StaticSource, parse_salary, posting_from_dict,
)


class TestSalaryParsing(unittest.TestCase):
    def test_k_notation_range(self):
        self.assertEqual(parse_salary("$120k - $160k"), (120_000, 160_000))

    def test_comma_notation(self):
        self.assertEqual(parse_salary("150,000 to 190,000"), (150_000, 190_000))

    def test_single_value(self):
        self.assertEqual(parse_salary("$130k"), (130_000, 130_000))

    def test_no_salary(self):
        self.assertEqual(parse_salary("competitive compensation"), (None, None))

    def test_ignores_bare_small_numbers(self):
        # "3 years" should not be read as a salary.
        self.assertEqual(parse_salary("3 years experience"), (None, None))

    def test_ignores_retirement_plan_tokens(self):
        # "401k" / "403(b)" must not be misread as $401k / $403k salaries.
        self.assertEqual(parse_salary("Benefits include a 401k match"), (None, None))
        self.assertEqual(parse_salary("We offer 403(b) and PTO"), (None, None))

    def test_real_salary_survives_benefit_token(self):
        # A genuine salary alongside a 401k mention is still extracted cleanly.
        self.assertEqual(
            parse_salary("$140k-$180k plus 401k match"), (140_000, 180_000)
        )


class TestPostingFromDict(unittest.TestCase):
    def test_infers_remote_from_location(self):
        p = posting_from_dict({
            "title": "BD Lead", "company": "X", "url": "u",
            "location": "Remote (US)",
        })
        self.assertTrue(p.remote)

    def test_parses_salary_from_text(self):
        p = posting_from_dict({
            "title": "BD Lead", "company": "X", "url": "u",
            "salary": "$140k-$180k",
        })
        self.assertEqual((p.salary_min, p.salary_max), (140_000, 180_000))

    def test_parses_iso_date(self):
        p = posting_from_dict({
            "title": "BD", "company": "X", "url": "u", "posted_date": "2026-06-15",
        })
        self.assertEqual(p.posted_date, date(2026, 6, 15))


class TestSourcingAgent(unittest.TestCase):
    def _job(self, url):
        return JobPosting(title="BD Lead", company="Figure", url=url)

    def test_dedup_by_fingerprint(self):
        agent = SourcingAgent([
            StaticSource([self._job("https://x.com/1?utm=a")]),
            StaticSource([self._job("https://x.com/1")]),  # same role, tracking param
        ])
        self.assertEqual(len(agent.collect()), 1)

    def test_drops_incomplete_postings(self):
        agent = SourcingAgent([
            StaticSource([JobPosting(title="", company="X", url="u")]),
        ])
        self.assertEqual(agent.collect(), [])

    def test_one_bad_source_does_not_sink_run(self):
        class Boom:
            name = "boom"
            def fetch(self):
                raise RuntimeError("api down")
        agent = SourcingAgent([Boom(), StaticSource([self._job("https://x.com/9")])])
        self.assertEqual(len(agent.collect()), 1)


if __name__ == "__main__":
    unittest.main()
