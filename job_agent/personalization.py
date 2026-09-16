"""Agent 3 - Personalization (the highest-ROI piece).

Given the candidate's master resume, a scored job, and the search profile, this
agent produces three artefacts per role: tailored resume bullets, a short cover
message, and a 1-2 sentence LinkedIn outreach line. It uses the Claude engine
when one is wired in, and falls back to a strong template engine that mines the
job description for keywords so it always produces usable collateral offline.
"""

from __future__ import annotations

import re
from typing import Optional

from job_agent.config import SearchProfile
from job_agent.llm import LLMEngine, HeuristicEngine, keywords
from job_agent.models import ApplicationKit, ScoredJob


_RESUME_SYSTEM = (
    "You are an elite executive resume writer. You rewrite resume bullets to "
    "mirror a target job, foregrounding quantified BD wins, revenue, "
    "partnerships, operations and strategy, and crypto/fintech relevance. "
    "Be concise and results-driven. Return 3-5 bullets, one per line, each "
    "starting with '- '."
)
_OUTREACH_SYSTEM = (
    "You write short, confident, entrepreneurial LinkedIn outreach messages to "
    "hiring managers. 1-2 sentences max, direct, no fluff, no emojis."
)
_COVER_SYSTEM = (
    "You write tight, high-signal cover notes (3-4 sentences) that connect a "
    "candidate's track record to a specific role. Confident and specific."
)


class PersonalizationAgent:
    """Builds an :class:`ApplicationKit` for a scored job."""

    def __init__(
        self,
        master_resume: str,
        profile: Optional[SearchProfile] = None,
        engine: Optional[LLMEngine] = None,
    ) -> None:
        self.master_resume = master_resume
        self.profile = profile or SearchProfile()
        self.engine = engine or HeuristicEngine()

    def build(self, scored: ScoredJob) -> ApplicationKit:
        job = scored.job
        if isinstance(self.engine, HeuristicEngine):
            return self._build_heuristic(scored)
        return self._build_llm(scored)

    # --------------------------------------------------------------- LLM path
    def _build_llm(self, scored: ScoredJob) -> ApplicationKit:
        job = scored.job
        context = (
            f"CANDIDATE SUMMARY:\n{self.profile.candidate_summary}\n\n"
            f"MASTER RESUME:\n{self.master_resume}\n\n"
            f"TARGET ROLE: {job.title} at {job.company}\n"
            f"JOB DESCRIPTION:\n{job.description}\n"
        )
        bullets_raw = self.engine.complete(
            _RESUME_SYSTEM, context + "\nRewrite my resume bullets for this role.",
            max_tokens=512,
        )
        bullets = [
            line.lstrip("-* ").strip()
            for line in bullets_raw.splitlines()
            if line.strip().lstrip("-* ")
        ][:5]
        cover = self.engine.complete(
            _COVER_SYSTEM,
            context + "\nWrite a 3-4 sentence cover note for this role.",
            max_tokens=256,
        ).strip()
        contact = job.contact_name or "there"
        outreach = self.engine.complete(
            _OUTREACH_SYSTEM,
            context + f"\nWrite a LinkedIn message to {contact}.",
            max_tokens=120,
        ).strip()
        return ApplicationKit(
            job_id=job.id,
            resume_bullets=bullets or self._template_bullets(scored),
            cover_message=cover,
            outreach_message=outreach,
            engine=self.engine.name,
        )

    # --------------------------------------------------------- heuristic path
    def _build_heuristic(self, scored: ScoredJob) -> ApplicationKit:
        job = scored.job
        return ApplicationKit(
            job_id=job.id,
            resume_bullets=self._template_bullets(scored),
            cover_message=self._template_cover(scored),
            outreach_message=self._template_outreach(scored),
            engine="heuristic",
        )

    def _job_terms(self, scored: ScoredJob) -> list[str]:
        """Salient terms from the JD, biased toward the profile's vocabulary."""
        jd_terms = keywords(f"{scored.job.title} {scored.job.description}", limit=10)
        priority = [
            t for t in self.profile.industry_keywords + self.profile.bonus_keywords
            if t.lower() in (scored.job.title + " " + scored.job.description).lower()
        ]
        ordered = priority + [t for t in jd_terms if t not in priority]
        return ordered[:6] or jd_terms[:6]

    def _template_bullets(self, scored: ScoredJob) -> list[str]:
        terms = self._job_terms(scored)
        focus = ", ".join(terms[:3]) if terms else "the core mandate"
        company = scored.job.company
        return [
            f"Drove multi-million-dollar revenue growth through {focus} partnerships, "
            f"directly aligned to {company}'s mandate.",
            "Built and scaled BD and operations functions from zero, closing "
            "strategic deals across crypto and fintech markets.",
            f"Owned go-to-market and partnership strategy spanning {', '.join(terms[3:6]) or 'key verticals'}, "
            "shortening sales cycles and expanding pipeline.",
            "Navigated licensing and regulatory workstreams to launch new products "
            "in compliance-heavy environments.",
        ]

    def _template_cover(self, scored: ScoredJob) -> str:
        job = scored.job
        why = scored.reasons[0] if scored.reasons else "the scope of this role"
        return (
            f"I'm reaching out about the {job.title} role at {job.company}. "
            f"{self.profile.candidate_summary} "
            f"What drew me here: {why.lower()}. "
            "I'd welcome the chance to show how I'd drive partnerships and revenue from day one."
        )

    def _template_outreach(self, scored: ScoredJob) -> str:
        job = scored.job
        contact = job.contact_name or "Hi"
        greeting = f"Hi {job.contact_name}," if job.contact_name else "Hi there,"
        terms = self._job_terms(scored)
        edge = terms[0] if terms else "BD and operations"
        return (
            f"{greeting} I came across the {job.title} role at {job.company} and it lines up "
            f"tightly with my background in {edge}. Would love to connect if a quick chat is helpful."
        )
