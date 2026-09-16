"""Tests for Agent 3 - personalization (heuristic + LLM engine paths)."""

import unittest

from job_agent.config import SearchProfile
from job_agent.llm import LLMEngine
from job_agent.models import JobPosting, ScoredJob
from job_agent.personalization import PersonalizationAgent


def _scored(**kw):
    base = dict(title="Head of Business Development", company="Figure", url="u",
                description="Own partnerships and revenue for our crypto platform.",
                contact_name="Dana")
    base.update(kw)
    return ScoredJob(job=JobPosting(**base), score=9.0,
                     reasons=["Title matches target function: business development"])


class FakeEngine:
    """Stub LLM that records prompts and returns canned structured text."""
    name = "fake"

    def __init__(self):
        self.calls = []

    def complete(self, system, prompt, *, max_tokens=512):
        self.calls.append((system, prompt))
        if "resume bullets" in prompt:
            return "- Closed $40M in partnerships\n- Scaled BD from zero"
        if "LinkedIn message" in prompt:
            return "Hi Dana, your BD role looks like a strong fit."
        return "A concise cover note tailored to Figure."


class TestHeuristicPersonalization(unittest.TestCase):
    def setUp(self):
        self.agent = PersonalizationAgent("master resume text", SearchProfile())

    def test_produces_all_three_artifacts(self):
        kit = self.agent.build(_scored())
        self.assertTrue(kit.resume_bullets)
        self.assertTrue(kit.cover_message)
        self.assertTrue(kit.outreach_message)
        self.assertEqual(kit.engine, "heuristic")

    def test_outreach_addresses_named_contact(self):
        kit = self.agent.build(_scored(contact_name="Dana"))
        self.assertIn("Dana", kit.outreach_message)

    def test_outreach_handles_missing_contact(self):
        kit = self.agent.build(_scored(contact_name=None))
        self.assertIn("Hi there", kit.outreach_message)

    def test_cover_references_company(self):
        kit = self.agent.build(_scored())
        self.assertIn("Figure", kit.cover_message)


class TestLLMPersonalization(unittest.TestCase):
    def test_uses_engine_and_parses_bullets(self):
        engine = FakeEngine()
        agent = PersonalizationAgent("resume", SearchProfile(), engine=engine)
        kit = agent.build(_scored())
        self.assertEqual(kit.engine, "fake")
        self.assertEqual(kit.resume_bullets[0], "Closed $40M in partnerships")
        self.assertEqual(len(engine.calls), 3)  # bullets, cover, outreach

    def test_engine_satisfies_protocol(self):
        self.assertIsInstance(FakeEngine(), LLMEngine)


if __name__ == "__main__":
    unittest.main()
