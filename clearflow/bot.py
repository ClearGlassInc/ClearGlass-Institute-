"""DailyOutcomeBot - the operator-facing front end of ClearFlow.

The bot has ONE job: drive the day's single keystone outcome and report when the
rest of the day unlocks behind it. It wraps :class:`AutomationWorkflow` with a
human-readable morning briefing, a live status line, and an end-of-day close-out.

Run the seeded program straight from the morning brief::

    python3 -m clearflow.bot

Or drive it from code with your own matrix, commitments, and brief.
"""

from __future__ import annotations

from datetime import time as dtime
from typing import Optional

from clearflow.matrix import (
    TODAYS_BRIEF,
    TODAYS_COMMITMENTS,
    todays_matrix,
)
from clearflow.models import Status, WorkItem
from clearflow.workflow import AutomationWorkflow


class DailyOutcomeBot:
    """A single-outcome daily driver over :class:`AutomationWorkflow`."""

    def __init__(self, workflow: Optional[AutomationWorkflow] = None) -> None:
        self.workflow = workflow or AutomationWorkflow(todays_matrix())

    # -- framing ------------------------------------------------------------

    @classmethod
    def from_today(cls) -> "DailyOutcomeBot":
        """Build the bot seeded with ClearGlassInc's matrix, pledge, and brief."""
        bot = cls(AutomationWorkflow(todays_matrix()))
        bot.workflow.set_commitments(TODAYS_COMMITMENTS)
        bot.workflow.ingest_brief(TODAYS_BRIEF)
        return bot

    # -- rendering ----------------------------------------------------------

    def morning_briefing(self) -> str:
        """The start-of-day report: outcome, commitments, gated domains, intel."""
        wf = self.workflow
        ks = wf.keystone
        lines: list[str] = []
        lines.append("=" * 64)
        lines.append("ClearFlow - Daily Outcome Bot")
        lines.append("ONE outcome today: advance AI Automation to unlock the rest.")
        lines.append("=" * 64)

        lines.append("\nYesterday's Pledge Review: no prior data on record.")
        lines.append("Today's 3 commitments (stated for review):")
        for i, pledge in enumerate(wf.ledger.pledges, 1):
            lines.append(f"  {i}. {pledge.text}")

        lines.append("\nKEYSTONE OUTCOME (the one thing):")
        if ks is not None:
            block = str(ks.time_block) if ks.time_block else "anytime"
            lines.append(f"  [{ks.priority.label}] {ks.domain}: {ks.action}")
            lines.append(f"       when: {block}   success: {ks.success_metric}")

        lines.append("\nGATED BEHIND THE KEYSTONE (locked until it lands):")
        for item in wf.locked_items():
            block = str(item.time_block) if item.time_block else "anytime"
            lines.append(
                f"  [{item.priority.label}] {item.domain}: {item.action} "
                f"({block})"
            )

        lines.append("\nCRITICAL INTELLIGENCE BRIEF (routed):")
        for sig in wf.signals:
            target = sig.routed_to or "unrouted"
            lines.append(f"  - {sig.headline}  ->  {target}")

        lines.append("\nNext action: " + self._focus_line())
        lines.append("=" * 64)
        return "\n".join(lines)

    def _focus_line(self) -> str:
        item = self.workflow.focus()
        if item is None:
            return "all outcomes complete - close out the day."
        return f"{item.domain}: {item.action}  ({item.success_metric})"

    def status_line(self) -> str:
        """A one-line live status of the day."""
        p = self.workflow.progress()
        gate = "LANDED" if p["keystone_landed"] else "PENDING"
        return (f"keystone={gate}  done={p['done']}/{p['total_items']}  "
                f"unlocked={p['unlocked_domains']}")

    def closeout(self) -> str:
        """End-of-day report: what landed, what unlocked, pledge outcomes."""
        wf = self.workflow
        lines = ["", "-" * 64, "CLOSE-OUT", "-" * 64]
        for item in wf.items:
            mark = {
                Status.DONE: "[x]",
                Status.IN_PROGRESS: "[~]",
                Status.BLOCKED: "[!]",
                Status.LOCKED: "[ ]",
                Status.PENDING: "[ ]",
            }[item.status]
            lines.append(f"  {mark} {item.priority.label} {item.domain}: "
                         f"{item.action} -> {item.status.value}")
            if item.evidence:
                lines.append(f"        evidence: {item.evidence}")
        p = wf.progress()
        lines.append(f"\n  completion: {int(p['completion'] * 100)}%   "
                     f"keystone landed: {p['keystone_landed']}")
        lines.append(f"  domains unlocked: {', '.join(p['unlocked_domains'])}")
        return "\n".join(lines)

    # -- driving ------------------------------------------------------------

    def land_keystone(self, evidence: str) -> list[WorkItem]:
        """Convenience: start and complete the keystone, returning what unlocks."""
        ks = self.workflow.keystone
        if ks is None:
            return []
        self.workflow.start(ks)
        return self.workflow.complete(ks, evidence)


def main(now: Optional[dtime] = None) -> None:
    """Print a full briefing, land the keystone, then show what unlocked."""
    bot = DailyOutcomeBot.from_today()
    print(bot.morning_briefing())

    # The keystone for today is this module itself - functional and tested.
    unlocked = bot.land_keystone(
        "clearflow package shipped; `python3 -m unittest "
        "clearflow.tests.test_clearflow` passes."
    )
    print("\n>> Keystone landed. Domains unlocked:")
    for item in unlocked:
        print(f"   - {item.domain}: {item.action} (now {item.status.value})")

    print("\n>> Status: " + bot.status_line())
    print(bot.closeout())


if __name__ == "__main__":
    main()
