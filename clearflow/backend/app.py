"""ClearFlow FastAPI gateway - drive the day over HTTP.

Mirrors ``clearpulse/backend/app.py``: a thin FastAPI surface adapting external
JSON to the stdlib engine and back. State is held in-process for the reference
path; a production deployment would persist via :mod:`clearflow.store` and run
the gateway as a stateless replica, with the :class:`EventBus` bridged to a
broker for the notifier fan-out.

Run::

    pip install -r clearflow/requirements.txt
    uvicorn clearflow.backend.app:app --reload
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from clearflow.bot import DailyOutcomeBot
from clearflow.events import EventBus
from clearflow.matrix import build_matrix
from clearflow.notify import CollectingNotifier
from clearflow.workflow import AutomationWorkflow, WorkflowError

app = FastAPI(title="ClearFlow Single-Outcome Day Gateway")

# Reference in-process state: one bot, one bus, one in-memory notifier feed.
_bus = EventBus()
_notifier = CollectingNotifier().attach(_bus)
_bot = DailyOutcomeBot.from_today()
_bot.workflow.bus = _bus


def _reset(workflow: AutomationWorkflow) -> None:
    global _bot
    workflow.bus = _bus
    _bot = DailyOutcomeBot(workflow)


class MatrixRow(BaseModel):
    priority: str
    domain: str
    action: str
    success_metric: str = ""
    time_block: Optional[str] = None
    effort_minutes: int = 60


class MatrixRequest(BaseModel):
    rows: list[MatrixRow]
    commitments: list[str] = []
    brief: list[str] = []


class LandRequest(BaseModel):
    evidence: str


def _find(trace_id: str):
    for item in _bot.workflow.items:
        if item.trace_id == trace_id:
            return item
    raise HTTPException(status_code=404, detail=f"No item {trace_id}")


@app.post("/v1/matrix")
def load_matrix(req: MatrixRequest) -> dict[str, Any]:
    """Replace the active matrix and (optionally) commitments + brief."""
    items = build_matrix([r.model_dump(exclude_none=True) for r in req.rows])
    workflow = AutomationWorkflow(items, bus=_bus)
    if req.commitments:
        workflow.set_commitments(req.commitments)
    if req.brief:
        workflow.ingest_brief(req.brief)
    _reset(workflow)
    return {"status": "loaded", "keystone": (
        _bot.workflow.keystone.to_dict() if _bot.workflow.keystone else None)}


@app.get("/v1/briefing")
def briefing() -> dict[str, Any]:
    return {"briefing": _bot.morning_briefing(), "status": _bot.status_line()}


@app.get("/v1/plan")
def plan() -> dict[str, Any]:
    wf = _bot.workflow
    cp = wf.critical_path()
    return {
        "execution_order": [i.action for i in wf.execution_order()],
        "critical_path": cp.actions(wf.items),
        "critical_path_minutes": cp.total_minutes,
    }


@app.post("/v1/items/{trace_id}/start")
def start_item(trace_id: str) -> dict[str, Any]:
    item = _find(trace_id)
    try:
        _bot.workflow.start(item)
    except WorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"status": "started", "item": item.to_dict()}


@app.post("/v1/items/{trace_id}/complete")
def complete_item(trace_id: str, req: LandRequest) -> dict[str, Any]:
    item = _find(trace_id)
    try:
        unlocked = _bot.workflow.complete(item, req.evidence)
    except WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "completed",
            "unlocked": [i.action for i in unlocked],
            "progress": _bot.workflow.progress()}


@app.post("/v1/keystone/land")
def land_keystone(req: LandRequest) -> dict[str, Any]:
    unlocked = _bot.land_keystone(req.evidence)
    return {"status": "landed", "unlocked": [i.action for i in unlocked],
            "progress": _bot.workflow.progress()}


@app.get("/v1/state")
def state() -> dict[str, Any]:
    return _bot.workflow.to_dict()


@app.get("/v1/events")
def events() -> dict[str, Any]:
    return {
        "events": [e.to_dict() for e in _bus.log],
        "notifications": _notifier.lines,
    }


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
