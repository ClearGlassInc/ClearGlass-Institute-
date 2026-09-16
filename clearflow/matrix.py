"""Strategic Priority Matrix construction.

A thin builder over :class:`~clearflow.models.WorkItem` that turns the daily
matrix - the P0/P1/P2 rows the operator writes each morning - into wired work
items. :func:`build_matrix` accepts plain dict rows so the matrix can come from
a CSV, a JSON config, or the literal table in the morning brief.

:func:`todays_matrix` seeds ClearGlassInc's matrix for the current day so the
demo and tests reproduce the exact program the bot was commissioned to run.
"""

from __future__ import annotations

from typing import Any

from clearflow.models import Priority, TimeBlock, WorkItem


def build_item(row: dict[str, Any]) -> WorkItem:
    """Build one :class:`WorkItem` from a matrix row.

    Recognised keys: ``priority``, ``domain``, ``action``, ``time_block``
    (free text like ``"8-10 AM"``), ``success_metric``, ``effort_minutes``.
    """
    block_text = row.get("time_block") or row.get("time")
    time_block = TimeBlock.parse(block_text) if block_text else None
    return WorkItem(
        domain=str(row["domain"]).strip(),
        action=str(row["action"]).strip(),
        priority=Priority.parse(row["priority"]),
        success_metric=str(row.get("success_metric", "")).strip(),
        time_block=time_block,
        effort_minutes=int(row.get("effort_minutes", 60)),
    )


def build_matrix(rows: list[dict[str, Any]]) -> list[WorkItem]:
    """Build an ordered matrix from rows (kept in declaration order)."""
    return [build_item(row) for row in rows]


# ClearGlassInc's matrix for the day this bot was commissioned. The P0 keystone
# is, fittingly, this very workflow module.
TODAYS_MATRIX: list[dict[str, Any]] = [
    {
        "priority": "P0",
        "domain": "AI Automation",
        "action": "Code core workflow module",
        "time_block": "8-10 AM",
        "success_metric": "Module functional, tested",
    },
    {
        "priority": "P1",
        "domain": "Cybersecurity",
        "action": "Review key vulnerabilities",
        "time_block": "10:30-11:30 AM",
        "success_metric": "Report with 3 fixes",
    },
    {
        "priority": "P2",
        "domain": "Personal Brand",
        "action": "LinkedIn post on AI trend",
        "time_block": "2-2:30 PM",
        "success_metric": "5+ engagements",
    },
]

# The three commitments the bot states for review (the morning pledge).
TODAYS_COMMITMENTS: list[str] = [
    "Ship the AI Automation core workflow module - functional and tested.",
    "Produce a cybersecurity review naming three concrete fixes.",
    "Publish one LinkedIn post on an AI trend and earn 5+ engagements.",
]

# The Critical Intelligence Brief headlines fed to the router.
TODAYS_BRIEF: list[str] = [
    "New AI agent tools accelerating automation.",
    "Rising supply chain cyber risks.",
    "Quantum error correction milestone.",
]


def todays_matrix() -> list[WorkItem]:
    """Return ClearGlassInc's seeded matrix as wired work items."""
    return build_matrix(TODAYS_MATRIX)
