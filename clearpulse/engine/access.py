"""Access Spike Detection - flag staff who suddenly touch many patient records.

The design doc uses per-user counting Bloom filters and distinct-patient
HyperLogLog sketches over a rolling 1-hour window. For the scaffold we keep an
exact rolling set of (timestamp, patient_id) tuples per user - correct and easy
to reason about - and leave a clear seam to swap in probabilistic sketches at
production scale. Deviation from the user's baseline is expressed as a Z-score.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta


class AccessSpikeDetector:
    """Tracks distinct patient access per user over a rolling window."""

    def __init__(
        self,
        window: timedelta = timedelta(hours=1),
        suspect_zscore: float = 3.0,
    ) -> None:
        self.window = window
        self.suspect_zscore = suspect_zscore
        self._events: dict[str, list[tuple[datetime, str]]] = defaultdict(list)

    def record(self, user_id: str, patient_id: str, ts: datetime) -> None:
        self._events[user_id].append((ts, patient_id))

    def _prune(self, user_id: str, now: datetime) -> None:
        cutoff = now - self.window
        self._events[user_id] = [
            (ts, pid) for ts, pid in self._events[user_id] if ts >= cutoff
        ]

    def distinct_count(self, user_id: str, now: datetime) -> int:
        """Distinct patient records this user touched within the window."""
        self._prune(user_id, now)
        return len({pid for _, pid in self._events[user_id]})

    @staticmethod
    def zscore(count: int, baseline_median: float, baseline_std: float) -> float:
        """Z-score of the current count against the user's 7-day baseline.

        A non-positive standard deviation means we have no spread to judge
        against, so we report 0.0 rather than dividing by zero.
        """
        if baseline_std <= 0:
            return 0.0
        return (count - baseline_median) / baseline_std

    def evaluate(
        self,
        user_id: str,
        now: datetime,
        baseline_median: float,
        baseline_std: float,
    ) -> dict[str, float | int | bool]:
        """Return the current count, its Z-score, and the snooping verdict."""
        count = self.distinct_count(user_id, now)
        z = self.zscore(count, baseline_median, baseline_std)
        return {
            "count": count,
            "zscore": z,
            "is_suspect": z >= self.suspect_zscore,
        }
