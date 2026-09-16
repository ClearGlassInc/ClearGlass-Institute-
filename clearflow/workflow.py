"""AutomationWorkflow - the ClearFlow core workflow module.

This is the orchestrator the daily P0 calls for: *code the core workflow module,
functional and tested*. It binds the matrix, the gatekeeper, the scheduler, the
pledge ledger, and the intel router into one object that enforces a single
contract:

    Advance exactly ONE keystone outcome per day; everything else stays gated
    until that outcome lands, then the rest of the day unlocks.

Like the sibling ``clearpulse`` pipeline, the seams here (gatekeeper, scheduler,
ledger, router) are swap points. The engine depends only on the standard
library so it runs without any optional service present.
"""

from __future__ import annotations

from datetime import time as dtime
from typing import Any, Optional

from clearflow.engine.gating import DomainGatekeeper
from clearflow.engine.graph import CriticalPath, DependencyGraph
from clearflow.engine.pledge import PledgeLedger
from clearflow.engine.scheduler import BlockScheduler
from clearflow.events import EventBus, EventType
from clearflow.intel.brief import IntelRouter
from clearflow.models import (
    IntelSignal,
    Priority,
    Status,
    WorkItem,
    utcnow,
)


class WorkflowError(RuntimeError):
    """Raised when a transition would violate the single-outcome contract."""


class AutomationWorkflow:
    """Drives one keystone outcome and unlocks domains behind it."""

    def __init__(
        self,
        items: Optional[list[WorkItem]] = None,
        *,
        gatekeeper: Optional[DomainGatekeeper] = None,
        scheduler: Optional[BlockScheduler] = None,
        ledger: Optional[PledgeLedger] = None,
        router: Optional[IntelRouter] = None,
        bus: Optional[EventBus] = None,
    ) -> None:
        self.items: list[WorkItem] = list(items or [])
        self.gatekeeper = gatekeeper or DomainGatekeeper()
        self.scheduler = scheduler or BlockScheduler()
        self.ledger = ledger or PledgeLedger()
        self.router = router or IntelRouter()
        # The event bus is optional: a bare workflow stays a pure state machine,
        # while supplying a bus lights up notifiers, history, and the runner.
        self.bus = bus
        self.signals: list[IntelSignal] = []
        if self.items:
            self.gatekeeper.wire_keystone_gate(self.items)

    def _emit(self, event_type: EventType, **payload: Any) -> None:
        if self.bus is not None:
            self.bus.emit(event_type, **payload)

    # -- construction -------------------------------------------------------

    def add_item(self, item: WorkItem) -> WorkItem:
        """Append a row to the matrix and re-wire the keystone gate."""
        self.items.append(item)
        self.gatekeeper.wire_keystone_gate(self.items)
        return item

    # -- focus & inspection -------------------------------------------------

    @property
    def keystone(self) -> Optional[WorkItem]:
        """The single outcome the whole day hangs on."""
        return self.gatekeeper.keystone(self.items)

    def focus(self, now: Optional[dtime] = None) -> Optional[WorkItem]:
        """The one item to work on right now (see :class:`BlockScheduler`)."""
        return self.scheduler.focus(self.items, now=now)

    def by_status(self, status: Status) -> list[WorkItem]:
        return [i for i in self.items if i.status == status]

    def locked_items(self) -> list[WorkItem]:
        return self.by_status(Status.LOCKED)

    def unlocked_domains(self) -> list[str]:
        """Domains with at least one startable (or done) item, in matrix order."""
        seen: list[str] = []
        for item in self.items:
            if item.status in (Status.LOCKED,):
                continue
            if item.domain not in seen:
                seen.append(item.domain)
        return seen

    def is_keystone_landed(self) -> bool:
        ks = self.keystone
        return ks is not None and ks.status == Status.DONE

    # -- transitions --------------------------------------------------------

    def start(self, item: WorkItem) -> WorkItem:
        """Begin work on an item. Enforces the single-outcome contract.

        Refuses to start a locked item, and refuses to start any non-keystone
        item while the keystone has not landed - that is the discipline the gate
        exists to protect.
        """
        if item.status == Status.LOCKED:
            blockers = self.gatekeeper.blocked_by(item, self.items)
            names = ", ".join(b.action for b in blockers) or "the keystone outcome"
            raise WorkflowError(
                f"'{item.action}' is locked until done: {names}"
            )
        if not item.is_keystone and not self.is_keystone_landed():
            raise WorkflowError(
                "Single-outcome rule: land the keystone "
                f"('{self.keystone.action if self.keystone else '?'}') "
                "before starting other domains."
            )
        item.status = Status.IN_PROGRESS
        self._emit(EventType.ITEM_STARTED, trace_id=item.trace_id,
                   domain=item.domain, action=item.action,
                   priority=item.priority.label)
        return item

    def complete(self, item: WorkItem, evidence: str) -> list[WorkItem]:
        """Mark an item done with success evidence; return newly unlocked items.

        Completing the keystone is the event that unlocks the rest of the day:
        the gatekeeper reconciles and flips every now-satisfied item to
        ``PENDING``.
        """
        if not evidence or not evidence.strip():
            raise WorkflowError(
                "Completion requires evidence against the success metric."
            )
        was_keystone_landed = self.is_keystone_landed()
        item.status = Status.DONE
        item.evidence = evidence.strip()
        item.completed_at = utcnow()
        self._emit(EventType.ITEM_COMPLETED, trace_id=item.trace_id,
                   domain=item.domain, action=item.action,
                   priority=item.priority.label)
        unlocked = self.gatekeeper.reconcile(self.items)
        # The keystone landing is the headline moment - announce it before the
        # individual domain unlocks so subscribers see cause then effect.
        if item.is_keystone and not was_keystone_landed:
            self._emit(EventType.KEYSTONE_LANDED, trace_id=item.trace_id,
                       domain=item.domain, action=item.action)
        for opened in unlocked:
            self._emit(EventType.DOMAIN_UNLOCKED, trace_id=opened.trace_id,
                       domain=opened.domain, action=opened.action,
                       priority=opened.priority.label)
        return unlocked

    def block(self, item: WorkItem, reason: str) -> WorkItem:
        """Park an item as BLOCKED with a reason (does not unlock dependents)."""
        item.status = Status.BLOCKED
        item.evidence = f"BLOCKED: {reason.strip()}"
        self._emit(EventType.ITEM_BLOCKED, trace_id=item.trace_id,
                   domain=item.domain, action=item.action, reason=reason.strip())
        return item

    # -- intel & pledges ----------------------------------------------------

    def ingest_brief(self, headlines: list[str]) -> list[IntelSignal]:
        """Route the Critical Intelligence Brief to domains and retain it."""
        self.signals = self.router.route(headlines)
        self._emit(EventType.BRIEF_INGESTED, count=len(self.signals),
                   routed=[s.routed_to for s in self.signals])
        return self.signals

    def signals_for(self, domain: str) -> list[IntelSignal]:
        return IntelRouter.for_domain(self.signals, domain)

    def set_commitments(self, texts: list[str]) -> list[Any]:
        """Set today's (capped) commitments via the pledge ledger."""
        pledges = self.ledger.commit_all(texts)
        self._emit(EventType.COMMITMENTS_SET, count=len(pledges))
        return pledges

    # -- dependency analysis ------------------------------------------------

    def graph(self) -> DependencyGraph:
        """A fresh :class:`DependencyGraph` over the current matrix wiring."""
        return DependencyGraph(self.items)

    def critical_path(self) -> CriticalPath:
        """The longest effort-weighted dependency chain - the day's lower bound."""
        return self.graph().critical_path()

    def execution_order(self) -> list[WorkItem]:
        """A valid dependency-respecting execution order for the matrix."""
        return self.graph().topological_order()

    # -- reporting ----------------------------------------------------------

    def progress(self) -> dict[str, Any]:
        """A compact snapshot of where the day stands."""
        total = len(self.items)
        done = len(self.by_status(Status.DONE))
        cp = self.critical_path()
        return {
            "total_items": total,
            "done": done,
            "completion": round(done / total, 3) if total else 0.0,
            "keystone_landed": self.is_keystone_landed(),
            "unlocked_domains": self.unlocked_domains(),
            "locked": [i.action for i in self.locked_items()],
            "critical_path": cp.actions(self.items),
            "critical_path_minutes": cp.total_minutes,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "keystone": self.keystone.to_dict() if self.keystone else None,
            "items": [i.to_dict() for i in self.items],
            "progress": self.progress(),
            "pledges": self.ledger.to_dict(),
            "signals": [s.to_dict() for s in self.signals],
        }
