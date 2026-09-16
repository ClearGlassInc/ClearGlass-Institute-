"""ClearFlow command-line interface.

A thin argparse front end over the bot so the engine is drivable without writing
Python::

    python3 -m clearflow briefing            # today's morning briefing
    python3 -m clearflow status               # one-line live status
    python3 -m clearflow plan                 # execution order + critical path
    python3 -m clearflow run                  # simulate the full day (async)
    python3 -m clearflow land "evidence..."   # land the keystone, show unlocks
    python3 -m clearflow history --store f.json   # streak + yesterday review

The CLI attaches a :class:`~clearflow.notify.ConsoleNotifier` so lifecycle
events are echoed as they fire.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import date

from clearflow.bot import DailyOutcomeBot
from clearflow.events import EventBus
from clearflow.notify import ConsoleNotifier
from clearflow.runner import simulate_day
from clearflow.store import DayRecord, HistoryStore
from clearflow.workflow import AutomationWorkflow


def _bot_with_bus() -> DailyOutcomeBot:
    bus = EventBus()
    ConsoleNotifier().attach(bus)
    bot = DailyOutcomeBot.from_today()
    bot.workflow.bus = bus
    return bot


def cmd_briefing(_: argparse.Namespace) -> int:
    print(DailyOutcomeBot.from_today().morning_briefing())
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    print(DailyOutcomeBot.from_today().status_line())
    return 0


def cmd_plan(_: argparse.Namespace) -> int:
    wf = DailyOutcomeBot.from_today().workflow
    print("Execution order (dependency-respecting):")
    for i, item in enumerate(wf.execution_order(), 1):
        print(f"  {i}. [{item.priority.label}] {item.domain}: {item.action} "
              f"({item.effort_minutes}m)")
    cp = wf.critical_path()
    print(f"\nCritical path ({cp.total_minutes}m): "
          + " -> ".join(cp.actions(wf.items)))
    return 0


def cmd_land(args: argparse.Namespace) -> int:
    bot = _bot_with_bus()
    evidence = args.evidence or "keystone landed via CLI"
    unlocked = bot.land_keystone(evidence)
    print(f"\nUnlocked {len(unlocked)} item(s).")
    print(bot.status_line())
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    bot = _bot_with_bus()
    reports = asyncio.run(simulate_day(bot.workflow, step_minutes=args.step))
    acted = [r for r in reports if r.action_taken != "idle"]
    print(f"\nSimulated {len(reports)} ticks; {len(acted)} actions taken.")
    print(bot.closeout())
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    store = HistoryStore(args.store)
    today = date.today().isoformat()
    summary = store.review_summary(before=today)
    print(json.dumps(summary, indent=2))
    if args.record:
        bot = DailyOutcomeBot.from_today()
        bot.land_keystone("recorded from CLI run")
        p = bot.workflow.progress()
        store.record(DayRecord(
            day=today,
            keystone_action=bot.workflow.keystone.action,
            keystone_landed=p["keystone_landed"],
            completion=p["completion"],
            domains_unlocked=p["unlocked_domains"],
            pledges=[{"text": pl.text, "outcome": pl.outcome.value}
                     for pl in bot.workflow.ledger.pledges],
        ))
        print(f"\nRecorded {today}; streak now {store.keystone_streak()}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clearflow", description="ClearFlow single-outcome day engine.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("briefing", help="print the morning briefing").set_defaults(
        func=cmd_briefing)
    sub.add_parser("status", help="print a one-line status").set_defaults(
        func=cmd_status)
    sub.add_parser("plan", help="print execution order + critical path").set_defaults(
        func=cmd_plan)

    land = sub.add_parser("land", help="land the keystone with evidence")
    land.add_argument("evidence", nargs="?", help="success evidence string")
    land.set_defaults(func=cmd_land)

    run = sub.add_parser("run", help="simulate the full day (async runner)")
    run.add_argument("--step", type=int, default=30, help="minutes per tick")
    run.set_defaults(func=cmd_run)

    hist = sub.add_parser("history", help="show streak + yesterday's review")
    hist.add_argument("--store", default=".clearflow_history.json",
                      help="path to the JSON history file")
    hist.add_argument("--record", action="store_true",
                      help="also record today's run into the store")
    hist.set_defaults(func=cmd_history)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
