"""Async day runner - drive the matrix forward as the clock advances.

The synchronous :class:`~clearflow.workflow.AutomationWorkflow` decides *what* is
allowed; this module decides *when* it happens. :class:`DayRunner` walks a clock
across the day's time blocks and, at each tick, surfaces the current focus item
and emits the lifecycle events the bus broadcasts.

It is built on :mod:`asyncio` with a pluggable :class:`Clock` so it can either
run against the wall clock (one tick per real interval) or *simulate* a whole day
in milliseconds for tests and demos - same code path, accelerated time.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, time as dtime, timedelta
from typing import Awaitable, Callable, Optional

from clearflow.events import EventType
from clearflow.models import Status
from clearflow.workflow import AutomationWorkflow


class Clock:
    """A virtual clock advancing in fixed steps over a [start, end) window."""

    def __init__(self, start: dtime, end: dtime, step_minutes: int = 30) -> None:
        self.start = start
        self.end = end
        self.step = timedelta(minutes=step_minutes)
        self._base = datetime(2000, 1, 1)

    def ticks(self) -> list[dtime]:
        """All clock times this clock will visit, ``start`` up to (not incl) ``end``."""
        out: list[dtime] = []
        cur = datetime.combine(self._base.date(), self.start)
        stop = datetime.combine(self._base.date(), self.end)
        while cur < stop:
            out.append(cur.time())
            cur += self.step
        return out


# An autopilot decides what to do with the current focus item at a tick. It
# returns one of: "start", "complete", "skip". Real operation leaves this None
# (a human acts); simulations pass an autopilot to drive the day unattended.
Autopilot = Callable[["DayRunner", Optional[object]], str]


@dataclass
class TickReport:
    """What happened on one tick - surfaced to the caller and to tests."""

    at: dtime
    focus_action: Optional[str]
    action_taken: str  # "start" | "complete" | "skip" | "idle"
    unlocked: list[str]


class DayRunner:
    """Advances an :class:`AutomationWorkflow` across a :class:`Clock`."""

    def __init__(
        self,
        workflow: AutomationWorkflow,
        clock: Clock,
        *,
        tick_seconds: float = 0.0,
    ) -> None:
        self.workflow = workflow
        self.clock = clock
        # Real-time pacing between ticks; 0 means "run as fast as possible".
        self.tick_seconds = tick_seconds
        self.reports: list[TickReport] = []

    async def run(self, autopilot: Optional[Autopilot] = None) -> list[TickReport]:
        """Walk the clock, optionally driving items via ``autopilot``.

        Without an autopilot the runner is observational: it emits the focus at
        each tick (useful for a live "what now?" feed). With one, it actually
        starts/completes items, respecting the workflow's single-outcome gate -
        attempts that violate the gate are caught and downgraded to ``skip``.
        """
        bus = self.workflow.bus
        if bus is not None:
            bus.emit(EventType.DAY_OPENED, ticks=len(self.clock.ticks()))

        for now in self.clock.ticks():
            focus = self.workflow.focus(now=now)
            action, unlocked = "idle", []
            if focus is not None and autopilot is not None:
                action, unlocked = self._apply(autopilot, focus)
            report = TickReport(
                at=now,
                focus_action=focus.action if focus else None,
                action_taken=action,
                unlocked=[i.action for i in unlocked] if unlocked else [],
            )
            self.reports.append(report)
            if self.tick_seconds:
                await asyncio.sleep(self.tick_seconds)

        return self.reports

    def _apply(self, autopilot: Autopilot, focus) -> tuple[str, list]:
        from clearflow.workflow import WorkflowError
        decision = autopilot(self, focus)
        try:
            if decision == "start" and focus.status != Status.IN_PROGRESS:
                self.workflow.start(focus)
                return "start", []
            if decision == "complete":
                if focus.status != Status.IN_PROGRESS:
                    self.workflow.start(focus)
                unlocked = self.workflow.complete(
                    focus, f"auto-completed at runtime: {focus.success_metric}")
                return "complete", unlocked
        except WorkflowError:
            return "skip", []
        return "skip", []


def eager_autopilot(runner: DayRunner, focus) -> str:
    """A simple autopilot: always drive the current focus item to completion.

    Because :meth:`DayRunner._apply` routes through the workflow's gate, this
    still completes items strictly in dependency order - the keystone first,
    then whatever it unlocks - even though the policy itself is naive.
    """
    return "complete"


async def simulate_day(
    workflow: AutomationWorkflow,
    *,
    start: dtime = dtime(8, 0),
    end: dtime = dtime(18, 0),
    step_minutes: int = 30,
) -> list[TickReport]:
    """Run an entire accelerated day unattended; returns the per-tick reports."""
    clock = Clock(start, end, step_minutes=step_minutes)
    runner = DayRunner(workflow, clock)
    return await runner.run(eager_autopilot)
