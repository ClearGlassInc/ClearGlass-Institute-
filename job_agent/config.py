"""Search profile and tuning knobs for the Job Automation Agent stack.

A :class:`SearchProfile` captures *who you are and what you want* - the role
keywords, industry focus, salary floor, and the candidate summary used to
personalise applications. Everything the agents need to make decisions lives
here so the behaviour is configurable without touching agent code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any


# Default targeting derived from the design brief: BD / strategy / operations /
# partnerships in crypto / fintech / web3, remote-friendly, $100k+.
_DEFAULT_ROLE_KEYWORDS = [
    "business development", "strategy", "operations", "partnerships",
    "bizdev", "growth", "revenue",
]
_DEFAULT_INDUSTRY_KEYWORDS = [
    "crypto", "fintech", "web3", "blockchain", "defi", "digital assets",
]
_DEFAULT_BONUS_KEYWORDS = [
    "licensing", "regulatory", "entrepreneur", "founder", "go-to-market",
    "gtm", "stablecoin", "payments",
]


@dataclass
class ScoringWeights:
    """Point budget for the heuristic scorer (sums conceptually to ~10).

    Each band contributes up to its weight; the LLM scorer, when enabled, is
    blended against these so scores stay comparable across engines.
    """

    role_match: float = 3.5
    industry_match: float = 3.0
    salary: float = 2.0
    remote: float = 1.0
    bonus: float = 1.5
    freshness: float = 1.0


@dataclass
class SearchProfile:
    """The candidate + targeting configuration the whole stack runs against."""

    candidate_name: str = "Candidate"
    headline: str = "Business Development & Operations Leader"
    candidate_summary: str = (
        "Entrepreneurial BD and operations leader with a track record of "
        "closing partnerships, scaling revenue, and standing up new lines of "
        "business in crypto and fintech."
    )
    role_keywords: list[str] = field(default_factory=lambda: list(_DEFAULT_ROLE_KEYWORDS))
    industry_keywords: list[str] = field(default_factory=lambda: list(_DEFAULT_INDUSTRY_KEYWORDS))
    bonus_keywords: list[str] = field(default_factory=lambda: list(_DEFAULT_BONUS_KEYWORDS))
    salary_floor: int = 100_000
    require_remote: bool = False
    min_score: float = 7.0
    daily_top_n: int = 10
    follow_up_days: int = 4
    weights: ScoringWeights = field(default_factory=ScoringWeights)

    # ------------------------------------------------------------------ I/O
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchProfile":
        weights = data.get("weights")
        profile = cls(**{k: v for k, v in data.items() if k != "weights"})
        if isinstance(weights, dict):
            profile.weights = ScoringWeights(**weights)
        return profile

    @classmethod
    def load(cls, path: str) -> "SearchProfile":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
