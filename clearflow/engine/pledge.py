"""Pledge ledger - today's commitments and yesterday's review.

The daily operating model asks two questions every morning: *did I keep
yesterday's word?* and *what are today's three commitments?* This ledger holds
both. It caps the day at three pledges on purpose - the same focus discipline
the gate enforces on work items applies to commitments.
"""

from __future__ import annotations

from typing import Any

from clearflow.models import Pledge, PledgeOutcome

MAX_DAILY_PLEDGES = 3


class PledgeLedger:
    """A bounded list of daily commitments with a next-day review."""

    def __init__(self, max_pledges: int = MAX_DAILY_PLEDGES) -> None:
        self.max_pledges = max_pledges
        self.pledges: list[Pledge] = []

    def commit(self, text: str) -> Pledge:
        """Record one commitment for the day (raises past the daily cap)."""
        if len([p for p in self.pledges]) >= self.max_pledges:
            raise ValueError(
                f"Daily pledge cap is {self.max_pledges}; focus, don't sprawl."
            )
        pledge = Pledge(text=text.strip())
        self.pledges.append(pledge)
        return pledge

    def commit_all(self, texts: list[str]) -> list[Pledge]:
        """Set the day's commitments in one call (must be within the cap)."""
        if len(texts) > self.max_pledges:
            raise ValueError(
                f"{len(texts)} pledges exceeds the daily cap of {self.max_pledges}."
            )
        return [self.commit(t) for t in texts]

    def review(self, trace_id: str, outcome: PledgeOutcome,
               note: str | None = None) -> Pledge:
        """Score a prior pledge (KEPT / MISSED / PARTIAL) with an optional note."""
        for pledge in self.pledges:
            if pledge.trace_id == trace_id:
                pledge.outcome = outcome
                pledge.note = note
                return pledge
        raise KeyError(f"No pledge with trace_id {trace_id}")

    def kept_rate(self) -> float:
        """Fraction of reviewed pledges marked KEPT (0.0 if none reviewed)."""
        reviewed = [p for p in self.pledges if p.outcome != PledgeOutcome.OPEN]
        if not reviewed:
            return 0.0
        kept = sum(1 for p in reviewed if p.outcome == PledgeOutcome.KEPT)
        return kept / len(reviewed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pledges": [p.to_dict() for p in self.pledges],
            "kept_rate": round(self.kept_rate(), 3),
        }
