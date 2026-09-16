"""Agent 2 - Filtering + Scoring.

Scores each posting 1-10 for fit and returns the score *with its reasons*, then
applies the keep filters (score floor + salary gate) and returns the top-N for
the day. The default scorer is a transparent, deterministic heuristic; when an
LLM engine is wired in it is blended in so scores stay comparable.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from job_agent.config import SearchProfile
from job_agent.llm import LLMEngine
from job_agent.models import JobPosting, ScoredJob


def _contains_any(haystack: str, needles: list[str]) -> list[str]:
    hay = haystack.lower()
    return [n for n in needles if n.lower() in hay]


class ScoringAgent:
    """Turns raw postings into ranked, filtered :class:`ScoredJob` records."""

    def __init__(
        self,
        profile: Optional[SearchProfile] = None,
        engine: Optional[LLMEngine] = None,
    ) -> None:
        self.profile = profile or SearchProfile()
        self.engine = engine  # optional; heuristic path needs none

    # ------------------------------------------------------------------ score
    def score_one(self, job: JobPosting, *, today: Optional[date] = None) -> ScoredJob:
        """Compute a 0-10 fit score with an explainable component breakdown."""
        w = self.profile.weights
        text = f"{job.title} {job.description} {job.location}"
        components: dict[str, float] = {}
        reasons: list[str] = []

        # Role keywords - title hits count double versus body hits.
        title_hits = _contains_any(job.title, self.profile.role_keywords)
        body_hits = _contains_any(job.description, self.profile.role_keywords)
        role_strength = min(1.0, (len(title_hits) * 2 + len(body_hits)) / 4.0)
        components["role_match"] = round(w.role_match * role_strength, 2)
        if title_hits:
            reasons.append(f"Title matches target function: {', '.join(title_hits)}")
        elif body_hits:
            reasons.append(f"Role keywords present: {', '.join(body_hits[:3])}")

        # Industry focus.
        ind_hits = _contains_any(text, self.profile.industry_keywords)
        ind_strength = min(1.0, len(ind_hits) / 2.0)
        components["industry_match"] = round(w.industry_match * ind_strength, 2)
        if ind_hits:
            reasons.append(f"Industry fit: {', '.join(sorted(set(ind_hits))[:3])}")

        # Salary gate / strength.
        top = job.salary_top
        if top is not None:
            if top >= self.profile.salary_floor:
                components["salary"] = w.salary
                reasons.append(f"Salary ${top:,} clears the ${self.profile.salary_floor:,} floor")
            else:
                # Partial credit scaled toward the floor.
                components["salary"] = round(w.salary * (top / self.profile.salary_floor), 2)
                reasons.append(f"Salary ${top:,} below target floor")
        else:
            components["salary"] = round(w.salary * 0.4, 2)  # unknown: neutral-ish

        # Remote.
        if job.remote:
            components["remote"] = w.remote
            reasons.append("Remote-friendly")
        else:
            components["remote"] = 0.0

        # Bonus weighting (licensing, founder, gtm, ...).
        bonus_hits = _contains_any(text, self.profile.bonus_keywords)
        components["bonus"] = round(min(w.bonus, 0.5 * len(bonus_hits)), 2)
        if bonus_hits:
            reasons.append(f"Edge signals: {', '.join(sorted(set(bonus_hits))[:3])}")

        # Freshness - decays over a two-week window.
        components["freshness"] = self._freshness(job, today)

        raw = sum(components.values())
        max_possible = (
            w.role_match + w.industry_match + w.salary + w.remote + w.bonus + w.freshness
        )
        score = round(10.0 * raw / max_possible, 2) if max_possible else 0.0
        return ScoredJob(job=job, score=score, reasons=reasons[:3], components=components)

    def _freshness(self, job: JobPosting, today: Optional[date]) -> float:
        w = self.profile.weights.freshness
        if not job.posted_date:
            return round(w * 0.5, 2)
        ref = today or date.today()
        age = (ref - job.posted_date).days
        if age <= 2:
            return w
        if age >= 14:
            return 0.0
        return round(w * (1 - (age - 2) / 12.0), 2)

    # ------------------------------------------------------------- filter/rank
    def rank(self, jobs: list[JobPosting], *, today: Optional[date] = None) -> list[ScoredJob]:
        """Score, apply keep filters, and return the day's top-N sorted desc."""
        scored = [self.score_one(j, today=today) for j in jobs]
        kept = [
            s for s in scored
            if s.score >= self.profile.min_score and self._passes_salary_gate(s.job)
        ]
        kept.sort(key=lambda s: s.score, reverse=True)
        return kept[: self.profile.daily_top_n]

    def _passes_salary_gate(self, job: JobPosting) -> bool:
        """Keep unknown-salary roles; reject only those proven below the floor."""
        top = job.salary_top
        if top is None:
            return True
        return top >= self.profile.salary_floor
