"""Domain gating - the rule that makes ClearFlow a *single-outcome* engine.

The whole point of the daily operating model is focus: advance the one keystone
outcome (the single P0) and let it *unlock* the rest of the day. This module
encodes that as a small dependency gate.

Rules enforced here:

* A ``WorkItem`` may leave ``LOCKED`` only once every item in its ``depends_on``
  set has reached ``DONE``.
* Non-keystone items are wired to depend (directly or transitively) on the
  keystone, so no other domain can be started until the keystone lands.
* When the keystone completes, the gate re-evaluates and flips every now-
  satisfied item ``LOCKED`` -> ``PENDING`` - the moment other domains unlock.

The gate is intentionally idempotent: calling :meth:`DomainGatekeeper.reconcile`
repeatedly converges to the same state, which is what the orchestrator relies on
after every state change.
"""

from __future__ import annotations

from clearflow.models import Priority, Status, WorkItem


class DomainGatekeeper:
    """Opens domains as their blocking dependencies complete."""

    def wire_keystone_gate(self, items: list[WorkItem]) -> None:
        """Make every non-keystone item depend on the single keystone outcome.

        This is what turns a flat priority list into a *one outcome unlocks the
        rest* program. The keystone is the lowest-priority-value P0 item; if no
        explicit dependency edges exist, every other item gains an edge to it
        and starts ``LOCKED``.
        """
        keystone = self.keystone(items)
        if keystone is None:
            return
        for item in items:
            if item is keystone:
                continue
            if keystone.trace_id not in item.depends_on:
                item.depends_on.append(keystone.trace_id)
            # Anything gated behind the keystone starts locked.
            if item.status == Status.PENDING:
                item.status = Status.LOCKED
        self.reconcile(items)

    @staticmethod
    def keystone(items: list[WorkItem]) -> WorkItem | None:
        """Return the day's single keystone outcome (the highest-rank P0).

        Ties (multiple P0s) resolve to the earliest-created item, so the model
        always commits to exactly *one* outcome even if the matrix lists several.
        """
        p0s = [i for i in items if i.priority == Priority.P0]
        pool = p0s or items
        if not pool:
            return None
        return min(pool, key=lambda i: (i.priority, i.created_at))

    def reconcile(self, items: list[WorkItem]) -> list[WorkItem]:
        """Unlock every item whose dependencies are all ``DONE``.

        Idempotent and order-independent: returns the items that transitioned
        from ``LOCKED`` to ``PENDING`` on this pass (empty once converged).
        """
        done_ids = {i.trace_id for i in items if i.status == Status.DONE}
        unlocked: list[WorkItem] = []
        for item in items:
            if item.status != Status.LOCKED:
                continue
            if all(dep in done_ids for dep in item.depends_on):
                item.status = Status.PENDING
                unlocked.append(item)
        return unlocked

    @staticmethod
    def blocked_by(item: WorkItem, items: list[WorkItem]) -> list[WorkItem]:
        """Return the not-yet-done items keeping ``item`` locked."""
        by_id = {i.trace_id: i for i in items}
        return [by_id[dep] for dep in item.depends_on
                if dep in by_id and by_id[dep].status != Status.DONE]
