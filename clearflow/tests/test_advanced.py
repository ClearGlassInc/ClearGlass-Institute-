"""Tests for the advanced ClearFlow subsystems.

Covers the event bus, the dependency-graph / critical-path engine, the notifier
seam, durable history (streaks + carryover), and the async day runner. Standard
library only::

    python3 -m unittest clearflow.tests.test_advanced -v
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from datetime import time as dtime

from clearflow.engine.graph import CycleError, DependencyGraph
from clearflow.events import EventBus, EventType
from clearflow.matrix import build_matrix, todays_matrix
from clearflow.models import Priority, Status, WorkItem
from clearflow.notify import CollectingNotifier, DigestNotifier, render
from clearflow.runner import Clock, DayRunner, eager_autopilot, simulate_day
from clearflow.store import DayRecord, HistoryStore
from clearflow.workflow import AutomationWorkflow


def _wf(bus: EventBus | None = None) -> AutomationWorkflow:
    return AutomationWorkflow(todays_matrix(), bus=bus)


# ---------------------------------------------------------------------------
# Event bus
# ---------------------------------------------------------------------------

class EventBusTests(unittest.TestCase):
    def test_emit_delivers_to_typed_and_wildcard(self):
        bus = EventBus()
        seen_typed: list = []
        seen_all: list = []
        bus.subscribe(EventType.ITEM_STARTED, lambda e: seen_typed.append(e))
        bus.subscribe(None, lambda e: seen_all.append(e))
        bus.emit(EventType.ITEM_STARTED, action="x")
        bus.emit(EventType.DAY_CLOSED)
        self.assertEqual(len(seen_typed), 1)
        self.assertEqual(len(seen_all), 2)

    def test_handler_errors_are_isolated(self):
        bus = EventBus()
        good: list = []
        bus.subscribe(EventType.DAY_OPENED, lambda e: (_ for _ in ()).throw(ValueError("boom")))
        bus.subscribe(EventType.DAY_OPENED, lambda e: good.append(e))
        bus.emit(EventType.DAY_OPENED)
        self.assertEqual(len(good), 1)            # second handler still ran
        self.assertEqual(len(bus.dead_letters), 1)  # first was captured

    def test_workflow_emits_keystone_then_unlocks(self):
        bus = EventBus()
        wf = _wf(bus)
        wf.start(wf.keystone)
        wf.complete(wf.keystone, "done")
        types = [e.type for e in bus.log]
        self.assertIn(EventType.KEYSTONE_LANDED, types)
        # Keystone landing precedes the domain unlock events.
        ks_idx = types.index(EventType.KEYSTONE_LANDED)
        unlock_idx = types.index(EventType.DOMAIN_UNLOCKED)
        self.assertLess(ks_idx, unlock_idx)
        self.assertEqual(len(bus.events_of(EventType.DOMAIN_UNLOCKED)), 2)


# ---------------------------------------------------------------------------
# Dependency graph / critical path
# ---------------------------------------------------------------------------

class GraphTests(unittest.TestCase):
    def test_topological_order_respects_dependencies(self):
        wf = _wf()
        order = wf.execution_order()
        positions = {i.trace_id: n for n, i in enumerate(order)}
        for item in wf.items:
            for dep in item.depends_on:
                self.assertLess(positions[dep], positions[item.trace_id])

    def test_keystone_first_in_order(self):
        wf = _wf()
        self.assertTrue(wf.execution_order()[0].is_keystone)

    def test_cycle_detected(self):
        a = WorkItem("D", "a", Priority.P0, "m")
        b = WorkItem("D", "b", Priority.P1, "m")
        a.depends_on.append(b.trace_id)
        b.depends_on.append(a.trace_id)
        graph = DependencyGraph([a, b])
        self.assertTrue(graph.has_cycle())
        with self.assertRaises(CycleError):
            graph.topological_order()

    def test_critical_path_is_longest_effort_chain(self):
        rows = [
            {"priority": "P0", "domain": "A", "action": "ks", "effort_minutes": 120},
            {"priority": "P1", "domain": "B", "action": "long", "effort_minutes": 90},
            {"priority": "P2", "domain": "C", "action": "short", "effort_minutes": 10},
        ]
        wf = AutomationWorkflow(build_matrix(rows))
        cp = wf.critical_path()
        # Both P1/P2 hang off the keystone, so the path is ks -> long = 210.
        self.assertEqual(cp.total_minutes, 210)
        self.assertEqual(cp.actions(wf.items), ["ks", "long"])

    def test_ready_set_after_keystone(self):
        wf = _wf()
        self.assertEqual([i.action for i in wf.graph().ready_set()],
                         [wf.keystone.action])
        wf.start(wf.keystone)
        wf.complete(wf.keystone, "done")
        self.assertEqual(len(wf.graph().ready_set()), 2)


# ---------------------------------------------------------------------------
# Notifiers
# ---------------------------------------------------------------------------

class NotifierTests(unittest.TestCase):
    def test_collecting_notifier_captures_forwarded_events(self):
        bus = EventBus()
        notifier = CollectingNotifier().attach(bus)
        wf = _wf(bus)
        wf.start(wf.keystone)
        wf.complete(wf.keystone, "done")
        # KEYSTONE_LANDED and DOMAIN_UNLOCKED are forwarded by default; ITEM_STARTED is not.
        joined = "\n".join(notifier.lines)
        self.assertIn("Keystone landed", joined)
        self.assertIn("Unlocked", joined)
        self.assertNotIn("Started", joined)

    def test_render_is_stable_for_known_types(self):
        bus = EventBus()
        evt = bus.emit(EventType.DOMAIN_UNLOCKED, domain="Cyber", action="Review")
        self.assertIn("Cyber", render(evt))


class DigestNotifierTests(unittest.TestCase):
    def _run_day(self):
        bus = EventBus()
        digest = DigestNotifier().attach(bus)
        wf = _wf(bus)
        wf.start(wf.keystone)
        wf.complete(wf.keystone, "shipped")
        return digest, wf

    def test_digest_captures_full_stream(self):
        digest, _ = self._run_day()
        types = {e.type for e, _ in digest.entries}
        # Batcher sees the whole lifecycle, including non-interrupt events.
        self.assertIn(EventType.ITEM_STARTED, types)
        self.assertIn(EventType.KEYSTONE_LANDED, types)
        self.assertIn(EventType.DOMAIN_UNLOCKED, types)

    def test_render_subject_reflects_keystone(self):
        digest, _ = self._run_day()
        out = digest.render()
        self.assertIn("Keystone landed", out["subject"])
        self.assertIn("Cybersecurity", out["subject"])
        self.assertIn("keystone landed: True", out["body"])

    def test_render_subject_when_keystone_open(self):
        bus = EventBus()
        digest = DigestNotifier().attach(bus)
        wf = _wf(bus)
        wf.start(wf.keystone)  # started but never completed
        out = digest.render()
        self.assertIn("keystone still open", out["subject"])


# ---------------------------------------------------------------------------
# History store
# ---------------------------------------------------------------------------

class HistoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "hist.json")

    def test_record_roundtrip_and_atomic_persist(self):
        store = HistoryStore(self.path)
        store.record(DayRecord(day="2026-06-01", keystone_landed=True,
                               keystone_action="ship module"))
        # Reload from disk into a fresh instance.
        reloaded = HistoryStore(self.path)
        rec = reloaded.get("2026-06-01")
        self.assertIsNotNone(rec)
        self.assertTrue(rec.keystone_landed)

    def test_streak_counts_consecutive_landed_days(self):
        store = HistoryStore(self.path)
        store.record(DayRecord(day="2026-05-30", keystone_landed=True))
        store.record(DayRecord(day="2026-05-31", keystone_landed=True))
        store.record(DayRecord(day="2026-06-01", keystone_landed=False))
        store.record(DayRecord(day="2026-06-02", keystone_landed=True))
        self.assertEqual(store.keystone_streak(as_of="2026-06-02"), 1)
        self.assertEqual(store.keystone_streak(as_of="2026-05-31"), 2)

    def test_carryover_and_review_summary(self):
        store = HistoryStore(self.path)
        store.record(DayRecord(
            day="2026-06-01", keystone_landed=True, keystone_action="ship",
            pledges=[{"text": "kept one", "outcome": "KEPT"},
                     {"text": "missed one", "outcome": "MISSED"}]))
        self.assertEqual(store.carryover_pledges(before="2026-06-02"),
                         ["missed one"])
        summary = store.review_summary(before="2026-06-02")
        self.assertTrue(summary["has_prior"])
        self.assertEqual(summary["pledges_kept"], 1)
        self.assertEqual(summary["carryover"], ["missed one"])

    def test_corrupt_file_does_not_crash(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("{not valid json")
        store = HistoryStore(self.path)  # must not raise
        self.assertEqual(store.all_days(), [])


# ---------------------------------------------------------------------------
# Async runner
# ---------------------------------------------------------------------------

class RunnerTests(unittest.TestCase):
    def test_clock_ticks_cover_window(self):
        clock = Clock(dtime(8, 0), dtime(10, 0), step_minutes=30)
        self.assertEqual(clock.ticks(),
                         [dtime(8, 0), dtime(8, 30), dtime(9, 0), dtime(9, 30)])

    def test_simulate_day_drives_keystone_first(self):
        bus = EventBus()
        wf = _wf(bus)
        reports = asyncio.run(simulate_day(wf, step_minutes=30))
        self.assertTrue(wf.is_keystone_landed())
        # Everything reachable gets completed by end of day.
        self.assertEqual(wf.progress()["done"], len(wf.items))
        # The first completion event is the keystone.
        completed = bus.events_of(EventType.ITEM_COMPLETED)
        self.assertEqual(completed[0].payload["priority"], "P0")
        self.assertTrue(any(r.action_taken == "complete" for r in reports))

    def test_runner_observational_without_autopilot(self):
        wf = _wf()
        clock = Clock(dtime(8, 0), dtime(9, 0), step_minutes=30)
        runner = DayRunner(wf, clock)
        reports = asyncio.run(runner.run())  # no autopilot
        self.assertTrue(all(r.action_taken == "idle" for r in reports))
        self.assertFalse(wf.is_keystone_landed())

    def test_autopilot_respects_gate(self):
        # Even an eager autopilot cannot complete a P1 before the keystone:
        # the first tick targets the keystone (the only startable item).
        wf = _wf()
        clock = Clock(dtime(8, 0), dtime(8, 30), step_minutes=30)
        runner = DayRunner(wf, clock)
        asyncio.run(runner.run(eager_autopilot))
        self.assertTrue(wf.is_keystone_landed())


if __name__ == "__main__":
    unittest.main(verbosity=2)
