"""ClearPulse FastAPI gateway - the REST ingress for raw feeds and alerts.

Mirrors ``artemis/backend/app.py``: a thin FastAPI surface that adapts external
JSON to the stdlib pipeline and back. The pipeline holds in-process window/state
for the reference path; a production deployment would back it with Redis +
PostgreSQL and run the gateway as a stateless replica behind the API gateway.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from clearpulse.compliance.scanner import assert_paths_within_root
from clearpulse.pipeline import ClearPulsePipeline

app = FastAPI(title="ClearPulse Triage & Compliance Gateway")
pipeline = ClearPulsePipeline()


def _scan_root() -> str:
    """Subtree that ``/v1/compliance/scan`` is allowed to read.

    Defaults to the gateway's working directory so the reference deployment
    needs no extra configuration; set ``CLEARPULSE_SCAN_ROOT`` to point the
    scan at a dedicated at-rest data mount instead.
    """
    return os.environ.get("CLEARPULSE_SCAN_ROOT") or os.getcwd()


class EncounterBundle(BaseModel):
    patient_id: Optional[str] = None
    provider_id: Optional[str] = None
    dept: Optional[str] = None
    vip: bool = False
    procedures: Optional[list[dict[str, Any]]] = None
    # Allow raw FHIR Bundle pass-through.
    resourceType: Optional[str] = None
    entry: Optional[list[dict[str, Any]]] = None


class AccessLogEntry(BaseModel):
    user_id: str
    patient_id: str
    dept: str = "UNKNOWN"
    timestamp: str
    action: str = "record_open"
    baseline_median: float = 8.0
    baseline_std: float = 4.0


class ScanRequest(BaseModel):
    paths: list[str]


@app.post("/v1/encounters")
def ingest_encounter(bundle: EncounterBundle) -> dict[str, Any]:
    envelopes = pipeline.process_encounter(bundle.model_dump(exclude_none=True))
    return {"status": "accepted", "scored": [e.to_dict() for e in envelopes]}


@app.post("/v1/access")
def ingest_access(entry: AccessLogEntry) -> dict[str, Any]:
    payload = entry.model_dump()
    baseline_median = payload.pop("baseline_median")
    baseline_std = payload.pop("baseline_std")
    verdict = pipeline.process_access(
        payload, baseline_median=baseline_median, baseline_std=baseline_std,
    )
    return {"status": "accepted", "verdict": verdict}


@app.post("/v1/compliance/scan")
def run_scan(req: ScanRequest) -> dict[str, Any]:
    # The path list arrives from an untrusted caller; confine it to the
    # permitted subtree before any filesystem walk or read happens.
    try:
        assert_paths_within_root(req.paths, _scan_root())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    raised = pipeline.scan_paths(req.paths)
    return {"status": "completed", "alerts": [
        {"alert_id": a.alert_id, "alert_type": a.alert_type,
         "severity": a.severity, "summary": a.summary} for a in raised
    ]}


@app.get("/v1/alerts")
def list_alerts() -> dict[str, Any]:
    return {
        "alerts": [
            {"alert_id": a.alert_id, "alert_type": a.alert_type,
             "severity": a.severity, "summary": a.summary,
             "trace_id": a.trace_id, "user_id": a.user_id,
             "created_at": a.created_at.isoformat()}
            for a in pipeline.router.accepted
        ],
        "correlations": pipeline.router.correlations,
    }


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
