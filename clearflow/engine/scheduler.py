"""Time-block scheduling - resolves *what should I be doing right now?*

Pure helpers over the matrix's :class:`~clearflow.models.TimeBlock` windows. The
scheduler never overrides the gate: it only ranks startable work. If the current
clock falls inside a startable item's block, that item is surfaced first;
otherwise the highest-priority startable item is the default focus.
"""

from __future__ import annotations

from datetime import time as dtime

from clearflow.models import Status, WorkItem


class BlockScheduler:
    """Selects the focus item for a given wall-clock moment."""

    def startable(self, items: list[WorkItem]) -> list[WorkItem]:
        """Items that are unlocked and not yet done, in priority order."""
        ready = [i for i in items if i.status.is_startable
                 or i.status == Status.PENDING]
        return sorted(ready, key=lambda i: (i.priority, i.created_at))

    def current_block_item(
        self, items: list[WorkItem], now: dtime,
    ) -> WorkItem | None:
        """Highest-priority startable item whose time block contains ``now``."""
        in_block = [i for i in self.startable(items)
                    if i.time_block is not None and i.time_block.contains(now)]
        if not in_block:
            return None
        return min(in_block, key=lambda i: (i.priority, i.created_at))

    def focus(self, items: list[WorkItem], now: dtime | None = None) -> WorkItem | None:
        """The single thing to work on next.

        Preference order:
        1. An in-progress item (never thrash off something already started).
        2. The startable item whose time block is live right now.
        3. The highest-priority startable item overall.
        """
        in_progress = [i for i in items if i.status == Status.IN_PROGRESS]
        if in_progress:
            return min(in_progress, key=lambda i: (i.priority, i.created_at))
        if now is not None:
            live = self.current_block_item(items, now)
            if live is not None:
                return live
        ready = self.startable(items)
        return ready[0] if ready else None
