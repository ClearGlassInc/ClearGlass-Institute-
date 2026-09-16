from fastapi import FastAPI, Depends
from pydantic import BaseModel
from artemis.policy.guard import enforce_action_policy
from artemis.agents.orchestrator import run_mission_workflow

app = FastAPI(title="ClearGlassInc Artemis Gateway")


class IntelEvent(BaseModel):
    event_id: str
    mission_id: str
    payload: dict
    classification: str
    compartment_tags: list[str] = []


@app.post('/v1/intel/events')
async def ingest_event(event: IntelEvent):
    result = await run_mission_workflow(event.model_dump())
    return {"status": "accepted", "workflow": result}


class ActionApprovalRequest(BaseModel):
    action_type: str
    risk_score: float
    uncertainty: float
    cross_compartment: bool
    subject: dict


@app.post('/v1/actions/check')
async def check_action(req: ActionApprovalRequest):
    decision = enforce_action_policy(req.model_dump())
    return decision
