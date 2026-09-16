"""Alert Router - the dedup + correlation stage before the dashboard.

Mirrors the Rust ``Alert Router`` in the design doc: it subscribes to the
unified alert feed, suppresses near-duplicate alerts, and correlates an access
spike with a billing anomaly for the *same user* - a strong signal of a
compromised account. In production this writes to PostgreSQL and pushes over
WebSocket; the scaffold keeps an in-memory record list with the same semantics.
"""

from __future__ import annotations

from collections import deque
from datetime import timedelta
from typing import Optional

from clearpulse.models import Alert, utcnow

# Alert types that, when sharing a user, indicate a likely compromised account.
_BILLING_TYPES = {"TEMPORAL_BILLING_ANOMALY"}
_ACCESS_TYPES = {"SNOOPING_SUSPECT", "ACCESS_VOLUME_SPIKE"}


class AlertRouter:
    """Deduplicates and correlates alerts on the unified stream."""

    def __init__(
        self,
        dedup_window: timedelta = timedelta(minutes=5),
        correlation_window: timedelta = timedelta(minutes=5),
    ) -> None:
        self.dedup_window = dedup_window
        self.correlation_window = correlation_window
        self._recent: deque[Alert] = deque()
        self.accepted: list[Alert] = []
        self.correlations: list[dict] = []

    def _evict(self, now) -> None:
        horizon = now - max(self.dedup_window, self.correlation_window)
        while self._recent and self._recent[0].created_at < horizon:
            self._recent.popleft()

    def submit(self, alert: Alert) -> Optional[Alert]:
        """Accept an alert unless an identical one is within the dedup window.

        Returns the accepted alert, or ``None`` when suppressed as a duplicate.
        """
        now = alert.created_at or utcnow()
        self._evict(now)

        key = alert.dedup_key()
        for existing in self._recent:
            if existing.dedup_key() == key and \
                    (now - existing.created_at) <= self.dedup_window:
                return None

        self._recent.append(alert)
        self.accepted.append(alert)
        self._correlate(alert, now)
        return alert

    def _correlate(self, alert: Alert, now) -> None:
        if alert.user_id is None:
            return
        is_access = alert.alert_type in _ACCESS_TYPES
        is_billing = alert.alert_type in _BILLING_TYPES
        if not (is_access or is_billing):
            return
        want = _BILLING_TYPES if is_access else _ACCESS_TYPES
        for other in self._recent:
            if other is alert or other.user_id != alert.user_id:
                continue
            if other.alert_type in want and \
                    abs((now - other.created_at).total_seconds()) <= \
                    self.correlation_window.total_seconds():
                self.correlations.append({
                    "user_id": alert.user_id,
                    "hypothesis": "possible_compromised_account",
                    "alert_ids": sorted([alert.alert_id, other.alert_id]),
                    "alert_types": sorted([alert.alert_type, other.alert_type]),
                })
                return
