"""Unit tests for the ClearFlow core workflow module.

Run with::

    python3 -m unittest clearflow.tests.test_clearflow -v

Covers the single-outcome contract (the gate), time-block parsing/scheduling,
the pledge ledger cap and review, and intel routing - all standard library.
"""

from __future__ import annotations

import unittest
from datetime import time as dtime

from clearflow.engine.gating import DomainGatekeeper
from clearflow.engine.pledge import PledgeLedger
from clearflow.engine.scheduler import BlockScheduler
from clearflow.intel.brief import IntelRouter
from clearflow.matrix import build_matrix, todays_matrix
from clearflow.models import (
    Priority,
    Status,
    TimeBlock,
    WorkItem,
    new_trace_id,
)
from clearflow.workflow import AutomationWorkflow, WorkflowError


def _matrix() -> list[WorkItem]:
    return todays_matrix()


class TimeBlockTests(unittest.TestCase):
    def test_parse_simple_am(self):
        block = TimeBlock.parse("8-10 AM")
        self.assertEqual(block.start, dtime(8, 0))
        self.assertEqual(block.end, dtime(10, 0))

    def test_parse_with_minutes(self):
        block = TimeBlock.parse("10:30-11:30 AM")
        self.assertEqual(block.start, dtime(10, 30))
        self.assertEqual(block.end, dtime(11, 30))

    def test_parse_pm_and_half_hour(self):
        block = TimeBlock.parse("2-2:30 PM")
        self.assertEqual(block.start, dtime(14, 0))
        self.assertEqual(block.end, dtime(14, 30))

    def test_noon_and_midnight(self):
        self.assertEqual(TimeBlock.parse("12-1 PM").start, dtime(12, 0))
        self.assertEqual(TimeBlock.parse("12-1 AM").start, dtime(0, 0))

    def test_contains(self):
        block = TimeBlock.parse("8-10 AM")
        self.assertTrue(block.contains(dtime(9, 0)))
        self.assertFalse(block.contains(dtime(10, 0)))  # half-open
        self.assertFalse(block.contains(dtime(7, 59)))


class PriorityTests(unittest.TestCase):
    def test_parse_variants(self):
        self.assertEqual(Priority.parse("P0"), Priority.P0)
        self.assertEqual(Priority.parse("p2"), Priority.P2)
        self.assertEqual(Priority.parse(1), Priority.P1)
        self.assertEqual(Priority.parse(Priority.P0), Priority.P0)

    def test_sorts_keystone_first(self):
        items = _matrix()
        first = min(items, key=lambda i: i.priority)
        self.assertEqual(first.priority, Priority.P0)


class GatingTests(unittest.TestCase):
    def test_non_keystone_items_start_locked(self):
        wf = AutomationWorkflow(_matrix())
        locked = wf.locked_items()
        self.assertTrue(locked)
        self.assertTrue(all(not i.is_keystone for i in locked))
        # The keystone is never locked.
        self.assertNotEqual(wf.keystone.status, Status.LOCKED)

    def test_keystone_completion_unlocks_everything(self):
        wf = AutomationWorkflow(_matrix())
        self.assertTrue(wf.locked_items())
        wf.start(wf.keystone)
        unlocked = wf.complete(wf.keystone, "tested and shipped")
        self.assertEqual(len(unlocked), 2)  # the P1 and P2 open up
        self.assertEqual(wf.locked_items(), [])
        self.assertTrue(wf.is_keystone_landed())

    def test_reconcile_is_idempotent(self):
        items = _matrix()
        gate = DomainGatekeeper()
        gate.wire_keystone_gate(items)
        # Reconciling without completing anything unlocks nothing.
        self.assertEqual(gate.reconcile(items), [])
        self.assertEqual(gate.reconcile(items), [])

    def test_single_keystone_even_with_two_p0s(self):
        rows = [
            {"priority": "P0", "domain": "A", "action": "first", "time_block": "8-9 AM"},
            {"priority": "P0", "domain": "B", "action": "second", "time_block": "9-10 AM"},
        ]
        items = build_matrix(rows)
        gate = DomainGatekeeper()
        ks = gate.keystone(items)
        self.assertEqual(ks.action, "first")  # earliest created wins the tie


class SingleOutcomeContractTests(unittest.TestCase):
    def test_cannot_start_locked_item(self):
        wf = AutomationWorkflow(_matrix())
        p1 = next(i for i in wf.items if i.priority == Priority.P1)
        with self.assertRaises(WorkflowError):
            wf.start(p1)

    def test_cannot_start_other_domain_before_keystone(self):
        # Even a manually-unlocked item is refused while the keystone is open.
        wf = AutomationWorkflow(_matrix())
        p1 = next(i for i in wf.items if i.priority == Priority.P1)
        p1.status = Status.PENDING  # force-unlock to test the second guard
        with self.assertRaises(WorkflowError):
            wf.start(p1)

    def test_completion_requires_evidence(self):
        wf = AutomationWorkflow(_matrix())
        wf.start(wf.keystone)
        with self.assertRaises(WorkflowError):
            wf.complete(wf.keystone, "   ")

    def test_full_happy_path(self):
        wf = AutomationWorkflow(_matrix())
        wf.start(wf.keystone)
        wf.complete(wf.keystone, "module functional, tested")
        p1 = next(i for i in wf.items if i.priority == Priority.P1)
        wf.start(p1)  # now allowed
        wf.complete(p1, "report with 3 fixes")
        prog = wf.progress()
        self.assertEqual(prog["done"], 2)
        self.assertTrue(prog["keystone_landed"])


class SchedulerTests(unittest.TestCase):
    def test_focus_prefers_in_progress(self):
        wf = AutomationWorkflow(_matrix())
        ks = wf.keystone
        wf.start(ks)
        self.assertIs(wf.focus(), ks)

    def test_focus_picks_keystone_first_when_idle(self):
        wf = AutomationWorkflow(_matrix())
        self.assertIs(wf.focus(), wf.keystone)

    def test_current_block_item(self):
        sched = BlockScheduler()
        items = _matrix()
        # 09:00 is inside the keystone's 8-10 AM block.
        live = sched.current_block_item(items, dtime(9, 0))
        self.assertIsNotNone(live)
        self.assertEqual(live.priority, Priority.P0)


class PledgeLedgerTests(unittest.TestCase):
    def test_caps_at_three(self):
        ledger = PledgeLedger()
        ledger.commit_all(["a", "b", "c"])
        with self.assertRaises(ValueError):
            ledger.commit("d")

    def test_commit_all_rejects_over_cap(self):
        ledger = PledgeLedger()
        with self.assertRaises(ValueError):
            ledger.commit_all(["a", "b", "c", "d"])

    def test_review_and_kept_rate(self):
        from clearflow.models import PledgeOutcome
        ledger = PledgeLedger()
        p1, p2, _ = ledger.commit_all(["a", "b", "c"])
        ledger.review(p1.trace_id, PledgeOutcome.KEPT)
        ledger.review(p2.trace_id, PledgeOutcome.MISSED)
        self.assertAlmostEqual(ledger.kept_rate(), 0.5)

    def test_review_unknown_raises(self):
        from clearflow.models import PledgeOutcome
        ledger = PledgeLedger()
        with self.assertRaises(KeyError):
            ledger.review(new_trace_id(), PledgeOutcome.KEPT)


class IntelRoutingTests(unittest.TestCase):
    def test_routes_brief_to_domains(self):
        router = IntelRouter()
        signals = router.route([
            "New AI agent tools accelerating automation.",
            "Rising supply chain cyber risks.",
            "Quantum error correction milestone.",
        ])
        routes = {s.headline: s.routed_to for s in signals}
        self.assertEqual(
            routes["New AI agent tools accelerating automation."],
            "AI Automation",
        )
        self.assertEqual(
            routes["Rising supply chain cyber risks."], "Cybersecurity")
        self.assertEqual(
            routes["Quantum error correction milestone."], "Research")

    def test_for_domain_filter(self):
        router = IntelRouter()
        signals = router.route(["Rising supply chain cyber risks."])
        self.assertEqual(
            len(IntelRouter.for_domain(signals, "Cybersecurity")), 1)
        self.assertEqual(
            len(IntelRouter.for_domain(signals, "AI Automation")), 0)


class WorkflowReportingTests(unittest.TestCase):
    def test_to_dict_is_serializable(self):
        import json
        wf = AutomationWorkflow(_matrix())
        wf.ingest_brief(["New AI agent tools accelerating automation."])
        wf.set_commitments(["ship it"])
        json.dumps(wf.to_dict())  # must not raise

    def test_unlocked_domains_grows_after_keystone(self):
        wf = AutomationWorkflow(_matrix())
        before = wf.unlocked_domains()
        wf.start(wf.keystone)
        wf.complete(wf.keystone, "done")
        after = wf.unlocked_domains()
        self.assertGreater(len(after), len(before))


if __name__ == "__main__":
    unittest.main(verbosity=2)
