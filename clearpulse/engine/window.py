"""Short-lived sliding-window state for temporal correlation.

In production this is backed by RocksDB for crash recovery; here it is a plain
in-memory index keyed by patient so the overlap check stays O(active claims per
patient). Facts age out once their ``service_end`` falls behind the trailing
edge of the window.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from clearpulse.models import ObservableFact, utcnow


class SlidingWindowState:
    """Holds recently-seen procedure facts within a sliding time window."""

    def __init__(self, window: timedelta = timedelta(minutes=15)) -> None:
        self.window = window
        self._by_patient: dict[str, list[ObservableFact]] = defaultdict(list)

    def add(self, fact: ObservableFact) -> None:
        self._by_patient[fact.patient_id].append(fact)

    def prune(self, now: datetime | None = None) -> None:
        """Drop facts whose service window ended before the trailing edge."""
        cutoff = (now or utcnow()) - self.window
        for patient_id, facts in list(self._by_patient.items()):
            kept = [f for f in facts if f.service_end >= cutoff]
            if kept:
                self._by_patient[patient_id] = kept
            else:
                del self._by_patient[patient_id]

    def overlapping(self, fact: ObservableFact) -> list[ObservableFact]:
        """Return other active facts for the same patient that overlap in time.

        The probe fact itself (matched by trace id + cpt code) is excluded so a
        claim never overlaps with itself.
        """
        results: list[ObservableFact] = []
        for other in self._by_patient.get(fact.patient_id, []):
            if other is fact:
                continue
            if other.trace_id == fact.trace_id and other.cpt_code == fact.cpt_code:
                continue
            latest_start = max(fact.service_start, other.service_start)
            earliest_end = min(fact.service_end, other.service_end)
            if earliest_end > latest_start:
                results.append(other)
        return results

    def active_count(self) -> int:
        return sum(len(v) for v in self._by_patient.values())
