"""Durable day history - so the morning review reads real data, not a stub.

The first version of the bot said *"Yesterday's Pledge Review: no prior data."*
This module removes that excuse. It persists a :class:`DayRecord` per day as
JSON and answers the questions the morning briefing needs:

* What did yesterday's keystone and pledges actually resolve to?
* How long is the current keystone-landed streak?
* Which of yesterday's commitments went unkept and should **carry over**?

Persistence is a single JSON file written atomically (temp file + ``os.replace``)
so a crash mid-write never corrupts history. No database required; the file is
the swap point for a real store later.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Optional


@dataclass
class DayRecord:
    """An immutable end-of-day snapshot, keyed by ISO date."""

    day: str  # ISO date, e.g. "2026-06-02"
    keystone_action: Optional[str] = None
    keystone_landed: bool = False
    completion: float = 0.0
    domains_unlocked: list[str] = field(default_factory=list)
    # Each pledge: {"text": ..., "outcome": "KEPT"|"MISSED"|"PARTIAL"|"OPEN"}
    pledges: list[dict[str, Any]] = field(default_factory=list)
    closed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def unkept_pledges(self) -> list[str]:
        """Texts of pledges that did not resolve KEPT (carryover candidates)."""
        return [p["text"] for p in self.pledges
                if p.get("outcome") not in ("KEPT",)]


class HistoryStore:
    """Append/replace day records in a JSON file, with derived analytics."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._records: dict[str, DayRecord] = {}
        self._load()

    # -- persistence --------------------------------------------------------

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, ValueError):
            # A corrupt/empty file should not crash the morning; start fresh.
            return
        for day, payload in raw.get("days", {}).items():
            self._records[day] = DayRecord(**payload)

    def _flush(self) -> None:
        """Atomically write the whole store (temp file + os.replace)."""
        payload = {"days": {d: asdict(r) for d, r in self._records.items()}}
        directory = os.path.dirname(os.path.abspath(self.path)) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    # -- writing ------------------------------------------------------------

    def record(self, day_record: DayRecord) -> DayRecord:
        """Persist (or replace) a day's record."""
        self._records[day_record.day] = day_record
        self._flush()
        return day_record

    # -- reading ------------------------------------------------------------

    def get(self, day: str) -> Optional[DayRecord]:
        return self._records.get(day)

    def latest_before(self, day: str) -> Optional[DayRecord]:
        """The most recent recorded day strictly before ``day`` (the 'yesterday')."""
        earlier = sorted(d for d in self._records if d < day)
        return self._records[earlier[-1]] if earlier else None

    def all_days(self) -> list[DayRecord]:
        return [self._records[d] for d in sorted(self._records)]

    # -- analytics ----------------------------------------------------------

    def keystone_streak(self, *, as_of: Optional[str] = None) -> int:
        """Count consecutive most-recent days whose keystone landed.

        Walks newest-first; the streak ends at the first non-landed day. Gaps in
        the calendar do not break the streak (only recorded days count), which
        matches an operator who does not log weekends.
        """
        as_of = as_of or date.today().isoformat()
        streak = 0
        for day in sorted((d for d in self._records if d <= as_of), reverse=True):
            if self._records[day].keystone_landed:
                streak += 1
            else:
                break
        return streak

    def carryover_pledges(self, *, before: str) -> list[str]:
        """Unkept pledges from the most recent prior day - to roll into today."""
        prior = self.latest_before(before)
        return prior.unkept_pledges() if prior else []

    def review_summary(self, *, before: str) -> dict[str, Any]:
        """A ready-to-render summary of 'yesterday' for the morning briefing."""
        prior = self.latest_before(before)
        if prior is None:
            return {"has_prior": False}
        kept = sum(1 for p in prior.pledges if p.get("outcome") == "KEPT")
        return {
            "has_prior": True,
            "day": prior.day,
            "keystone_action": prior.keystone_action,
            "keystone_landed": prior.keystone_landed,
            "pledges_kept": kept,
            "pledges_total": len(prior.pledges),
            "carryover": prior.unkept_pledges(),
            "streak": self.keystone_streak(as_of=prior.day),
        }
