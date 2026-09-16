"""Self-contained ClearFlow demo - the single-outcome day, end to end.

Run with::

    python3 -m clearflow.demo

Requires no external services. It seeds ClearGlassInc's matrix, proves the gate
(other domains refuse to start before the keystone lands), lands the keystone,
and shows the rest of the day unlock.
"""

from __future__ import annotations

from clearflow.bot import DailyOutcomeBot
from clearflow.workflow import WorkflowError


def main() -> None:
    bot = DailyOutcomeBot.from_today()
    wf = bot.workflow

    print(bot.morning_briefing())

    print("\n== proving the gate: try to start a P1 before the keystone ==")
    p1 = next(i for i in wf.items if i.priority.name == "P1")
    try:
        wf.start(p1)
    except WorkflowError as exc:
        print(f"   refused (correct): {exc}")

    print("\n== landing the keystone ==")
    unlocked = bot.land_keystone(
        "clearflow module shipped and unit-tested."
    )
    for item in unlocked:
        print(f"   unlocked -> {item.domain}: {item.action} ({item.status.value})")

    print("\n== now the cybersecurity review starts, informed by routed intel ==")
    wf.start(p1)
    for sig in wf.signals_for(p1.domain):
        print(f"   intel for {p1.domain}: {sig.headline}")
    wf.complete(p1, "Report delivered: patch CVE-x, pin deps, enable SBOM scan.")

    print("\n== status ==")
    print("   " + bot.status_line())
    print(bot.closeout())


if __name__ == "__main__":
    main()
