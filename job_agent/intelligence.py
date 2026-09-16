"""Advanced upgrade - the Opportunity Intelligence Layer.

Analyses the tracker to surface where the pipeline is actually converting:
response rate by job type and salary band, fastest-moving companies, and
concrete recommendations. Pure aggregation over :class:`Application` rows, so it
needs no LLM, though a summary can be handed to one for narrative framing.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from job_agent.models import Application, ApplicationStatus

# Statuses that indicate the application got a positive reaction.
_RESPONDED = {ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER}
_TERMINAL = _RESPONDED | {ApplicationStatus.REJECTED}


def _band(salary_top: Any) -> str:
    if not salary_top:
        return "unknown"
    if salary_top < 100_000:
        return "<100k"
    if salary_top < 150_000:
        return "100-150k"
    if salary_top < 200_000:
        return "150-200k"
    return "200k+"


def _function(title: str) -> str:
    t = title.lower()
    for label, needles in (
        ("business development", ("business development", "bizdev", "bd ", "partnerships")),
        ("strategy", ("strategy", "strategic")),
        ("operations", ("operations", "ops")),
        ("growth", ("growth", "revenue")),
    ):
        if any(n in t for n in needles):
            return label
    return "other"


class IntelligenceLayer:
    """Computes conversion analytics and recommendations from tracker rows."""

    def analyze(self, applications: list[Application]) -> dict[str, Any]:
        considered = [a for a in applications if a.applied_date is not None]
        by_function: dict[str, dict[str, int]] = defaultdict(lambda: {"applied": 0, "responded": 0})
        by_band: dict[str, dict[str, int]] = defaultdict(lambda: {"applied": 0, "responded": 0})
        company_speed: dict[str, int] = defaultdict(int)

        for app in considered:
            fn = _function(app.job.title)
            band = _band(app.job.salary_top)
            by_function[fn]["applied"] += 1
            by_band[band]["applied"] += 1
            if app.status in _RESPONDED:
                by_function[fn]["responded"] += 1
                by_band[band]["responded"] += 1
                company_speed[app.job.company] += 1

        def rate(d: dict[str, int]) -> float:
            return round(d["responded"] / d["applied"], 3) if d["applied"] else 0.0

        function_stats = {fn: {**v, "response_rate": rate(v)} for fn, v in by_function.items()}
        band_stats = {b: {**v, "response_rate": rate(v)} for b, v in by_band.items()}

        return {
            "total_applied": len(considered),
            "total_responded": sum(1 for a in considered if a.status in _RESPONDED),
            "by_function": function_stats,
            "by_salary_band": band_stats,
            "fastest_responding_companies": sorted(
                company_speed, key=company_speed.get, reverse=True
            )[:5],
            "recommendations": self._recommend(function_stats, band_stats),
        }

    def _recommend(self, fn_stats: dict, band_stats: dict) -> list[str]:
        recs: list[str] = []
        if fn_stats:
            best_fn = max(fn_stats, key=lambda k: fn_stats[k]["response_rate"])
            if fn_stats[best_fn]["response_rate"] > 0:
                recs.append(
                    f"'{best_fn}' roles convert best "
                    f"({fn_stats[best_fn]['response_rate']:.0%}) - weight sourcing toward them."
                )
        if band_stats:
            best_band = max(band_stats, key=lambda k: band_stats[k]["response_rate"])
            if band_stats[best_band]["response_rate"] > 0:
                recs.append(
                    f"The {best_band} band responds most - prioritise those listings."
                )
        if not recs:
            recs.append("Not enough responses yet - keep volume up and revisit after ~15 applications.")
        return recs
