"""Dependency graph analysis - the math under the gate.

:class:`DomainGatekeeper` enforces the *keystone-first* rule for the common case.
This module generalises it: an arbitrary directed acyclic graph of work items
with cross-domain dependencies, so the engine can answer the questions a planner
actually asks:

* In what order *can* this day be executed? (topological sort, Kahn's algorithm)
* Did someone wire a contradictory dependency? (cycle detection)
* Which chain of work determines the earliest finish - the **critical path** -
  and how long is it? (longest weighted path by ``effort_minutes``)
* What is ready to start right now given what is already done? (ready set)

Everything here is a pure function of the item list and its ``depends_on`` edges;
no I/O, standard library only, fully unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from clearflow.models import Status, WorkItem


class CycleError(ValueError):
    """Raised when the dependency edges contain a cycle (no valid order)."""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        super().__init__("Dependency cycle: " + " -> ".join(cycle))


@dataclass(frozen=True)
class CriticalPath:
    """The longest dependency chain by total effort - the day's lower bound."""

    item_ids: list[str]
    total_minutes: int

    def actions(self, items: Iterable[WorkItem]) -> list[str]:
        by_id = {i.trace_id: i for i in items}
        return [by_id[tid].action for tid in self.item_ids if tid in by_id]


class DependencyGraph:
    """A DAG over work items keyed by ``trace_id``.

    The graph treats ``depends_on`` as edges *into* an item (predecessors must
    finish first). It is rebuilt from the item list each time so it always
    reflects current ``depends_on`` wiring.
    """

    def __init__(self, items: list[WorkItem]) -> None:
        self.items = items
        self.by_id = {i.trace_id: i for i in items}
        # Only keep edges whose endpoints both exist (defensive against stale ids).
        self.preds: dict[str, list[str]] = {
            i.trace_id: [d for d in i.depends_on if d in self.by_id]
            for i in items
        }
        self.succs: dict[str, list[str]] = {i.trace_id: [] for i in items}
        for node, deps in self.preds.items():
            for dep in deps:
                self.succs[dep].append(node)

    # -- ordering -----------------------------------------------------------

    def topological_order(self) -> list[WorkItem]:
        """Return items in a valid execution order (Kahn's algorithm).

        Ties are broken by ``(priority, created_at)`` so the keystone and higher
        priorities surface as early as their dependencies allow - a stable,
        meaningful order rather than an arbitrary one. Raises :class:`CycleError`
        if no topological order exists.
        """
        indegree = {tid: len(deps) for tid, deps in self.preds.items()}
        ready = [tid for tid, d in indegree.items() if d == 0]
        order: list[str] = []

        def sort_key(tid: str) -> tuple:
            item = self.by_id[tid]
            return (item.priority, item.created_at, tid)

        while ready:
            ready.sort(key=sort_key)
            node = ready.pop(0)
            order.append(node)
            for nxt in self.succs[node]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    ready.append(nxt)

        if len(order) != len(self.items):
            raise CycleError(self._find_cycle())
        return [self.by_id[tid] for tid in order]

    def _find_cycle(self) -> list[str]:
        """Recover one cycle for the error message (DFS with a recursion stack)."""
        WHITE, GREY, BLACK = 0, 1, 2
        color = {tid: WHITE for tid in self.by_id}
        stack: list[str] = []

        def visit(node: str) -> list[str] | None:
            color[node] = GREY
            stack.append(node)
            for nxt in self.succs[node]:
                if color[nxt] == GREY:
                    idx = stack.index(nxt)
                    return stack[idx:] + [nxt]
                if color[nxt] == WHITE:
                    found = visit(nxt)
                    if found:
                        return found
            stack.pop()
            color[node] = BLACK
            return None

        for tid in self.by_id:
            if color[tid] == WHITE:
                found = visit(tid)
                if found:
                    return [self.by_id[t].action for t in found]
        return []

    def has_cycle(self) -> bool:
        try:
            self.topological_order()
            return False
        except CycleError:
            return True

    # -- analysis -----------------------------------------------------------

    def ready_set(self) -> list[WorkItem]:
        """Items not done/blocked whose predecessors are all done."""
        done = {tid for tid, i in self.by_id.items() if i.status == Status.DONE}
        ready: list[WorkItem] = []
        for item in self.items:
            if item.status in (Status.DONE, Status.BLOCKED):
                continue
            if all(dep in done for dep in self.preds[item.trace_id]):
                ready.append(item)
        return sorted(ready, key=lambda i: (i.priority, i.created_at))

    def critical_path(self) -> CriticalPath:
        """Longest path by total ``effort_minutes`` over the DAG.

        Computed via DP in topological order: ``finish[n] = effort[n] +
        max(finish[p] for p in preds)``. The node with the greatest finish ends
        the critical path; we walk predecessors back to its root. This is the
        theoretical minimum wall-clock for the day if unrelated work runs in
        parallel - the chain you cannot compress.
        """
        order = self.topological_order()
        finish: dict[str, int] = {}
        choice: dict[str, str | None] = {}
        for item in order:
            tid = item.trace_id
            best_pred, best_val = None, 0
            for dep in self.preds[tid]:
                if finish[dep] > best_val:
                    best_pred, best_val = dep, finish[dep]
            finish[tid] = best_val + max(0, item.effort_minutes)
            choice[tid] = best_pred

        if not finish:
            return CriticalPath(item_ids=[], total_minutes=0)

        end = max(finish, key=lambda t: finish[t])
        chain: list[str] = []
        node: str | None = end
        while node is not None:
            chain.append(node)
            node = choice[node]
        chain.reverse()
        return CriticalPath(item_ids=chain, total_minutes=finish[end])
