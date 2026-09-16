# ClearGlassInc Artemis — Self-Evolving Intelligence Platform (Production Blueprint)

## System Architecture

---

## System Architecture

### 1.1 End-to-End Reference Architecture

```text
[External Feeds: ISR, cyber telemetry, HUMINT reports, partner APIs, archival batches]
        -> [Ingest Mesh: streaming connectors + batch loaders + schema guards]
        -> [Foundry Data Plane: bronze/silver/gold + ontology + lineage]
        -> [AIP Agent Plane: copilots, tools, evals, model routing]
        -> [Gotham Ops Plane: investigations, casework, entity tracking]
        -> [Mission Apps: command UI, analyst workbench, action approval board]
        -> [Apollo Control Plane: deploy, canary, rollback, policy promotion]
```

### 2) Layer-by-Layer Components

- **Frontend (Web/Mission UI)**: React + TypeScript + GraphQL + WebSockets.
- **API Gateway**: Envoy + FastAPI edge; mTLS, JWT validation, ABAC pre-check.
- **Backend Services (Python)**: case, entity, recommendation, approval, audit, and eval services.
- **Event/Streaming Layer**: Kafka + schema registry + exactly-once transactional consumers.
- **Data/Lakehouse**: Foundry datasets for governed ETL and ontology projection.
- **Search/Retrieval**: hybrid graph retrieval (ontology) + vector index (semantic evidence).
- **Model Router/Inference**: AIP routing policy across summarization/reasoning/extraction models.
- **Policy Layer**: OPA/Rego + Foundry policy bindings + mission-context ABAC.
- **Observability**: OpenTelemetry traces, structured logs, quality dashboards, drift dashboards.
- **Deployment Layer**: Apollo rings (dev/stage/prod), automated rollback on SLO/policy breach.

### 3) Control-Plane Interfaces

### 1) Learning signal capture

---

## Data and Ontology

### 1) Core Entity Types

```yaml
EntityTypes:
  Person: [person_id, aliases[], risk_score, confidence, clearance_tags[], valid_time, ingest_time]
  Organization: [org_id, type, sanctions_status, ownership_graph_ref]
  Device: [device_id, device_type, fingerprint, geostamp_history[]]
  Asset: [asset_id, class, owner_ref, mission_tags[]]
  Location: [loc_id, lat, lon, geofence_tags[]]
  Event: [event_id, event_type, severity, source_refs[], occurred_at]
  Signal: [signal_id, modality, payload_hash, detection_confidence]
  Case: [case_id, state, priority, assigned_team, legal_basis]
  Mission: [mission_id, coalition_scope, objective, constraints]
  Recommendation: [rec_id, rationale, confidence, policy_check_result]
  ActionPackage: [pkg_id, actions[], required_approvers[], execution_window]
```

### 2) Relationship Model

- `ASSOCIATED_WITH(Person, Organization)`
- `USES(Person, Device)`
- `LOCATED_AT(Entity, Location)` (temporal edge)
- `MENTIONED_IN(Entity, IntelReport)`
- `TRIGGERED(Event, Alert)`
- `RECOMMENDS(Recommendation, ActionPackage)`
- `APPROVED_BY(ActionPackage, Operator)`

All edges carry `confidence`, `evidence_refs`, `lineage_id`, `valid_time`, `classification_tags`.

### 3) Ontology Rules that Drive AI Behavior

- Agent retrieval context is generated from ontology neighborhood with mission- and classification-aware filtering.
- Tool calls are constrained by ontology type permissions (e.g., coalition A cannot traverse coalition B edges).
- Recommendation confidence is capped by weakest-link evidence confidence and policy constraints.
- Temporal reasoning defaults to bitemporal replay (`valid_time` vs `transaction_time`) for audit defensibility.

---

### 3) Event + storage + retrieval

### 3.1 Copilot Roles

1. **Analyst Copilot**
   - Entity history synthesis
   - Hypothesis generation with confidence intervals
   - Source-grounded evidence trails

### 1) Copilots

- **Analyst Copilot**: entity-centric narrative generation and evidence-backed hypotheses.
- **Commander Copilot**: mission impact forecasts, action prioritization, COA comparison.
- **Watchfloor Copilot**: live alert triage, duplicate suppression, escalation routing.

### 2) Multi-Agent DAG (AIP)

```text
ingest_event
  -> triage_agent
  -> enrich_agent
  -> correlate_agent
  -> summarize_agent
  -> recommend_agent
  -> policy_gate_agent
  -> human_approval_node
  -> action_package_dispatch (if approved)
```

### 3) Tooling Contracts

Agents can:
1. query Foundry datasets/ontology,
2. run graph traversals with bounded depth,
3. draft Gotham case updates,
4. generate intel products,
5. prepare action packages.

Agents cannot execute operationally significant actions without explicit human approval tokens.

---

## Self-Improvement Loop

### 1) Signal Capture

- operator edits to drafts (edit distance + semantic diff),
- accept/reject decisions,
- alert adjudication (TP/FP/FN),
- mission outcomes,
- latency/cost/tool-failure telemetry,
- policy denials and override requests.

### 1) FastAPI gateway with policy check

```text
Runtime Signals -> Feature Store -> Eval Dataset Builder -> Offline Evals
             -> Candidate Prompt/Workflow/Route Changes
             -> Risk Scoring + Policy Review
             -> Human Approval Board
             -> Apollo Canary Release
             -> Online Guarded A/B
             -> Promotion or Rollback
```

### 3) Safety Controls

- immutable versioning for prompts, tools, workflows, and route policies,
- two-person approval for high-impact upgrades,
- rollback to last known-good config in < 2 minutes,
- drift monitors on precision/recall/latency/policy-violations,
- automatic freeze if policy breaches exceed threshold.

### 4) Governance-Gated Self-Evolution

The platform may **propose** updates (prompt template changes, routing adjustments, heuristic thresholds), but only a human governance board may approve promotion into production.

---

async def opa_allow(subject: dict, action: str, resource: dict) -> bool:
    payload = {"input": {"subject": subject, "action": action, "resource": resource}}
    async with httpx.AsyncClient(timeout=2.0) as client:
        r = await client.post("http://opa:8181/v1/data/artemis/allow", json=payload)
        r.raise_for_status()
        return bool(r.json().get("result", False))

### 5.1 Web UI (TypeScript/React)

Screens:
- Mission dashboard
- Alert stream + triage queue
- Graph explorer + temporal timeline
- Copilot panel with “Why this?” provenance tab
- Recommendation approval/reject/revise workflow

Client architecture:
- `app-shell`
- `mission-state` (Redux Toolkit / Zustand)
- `live-stream` (SSE/WebSocket)
- `auth-context` (OIDC + mission claims)
- `policy-aware components` (hide/redact by ABAC decision)

### 5.2 API Gateway + Mission Services (Python/FastAPI)

Core APIs:
- `POST /api/alerts/ingest`
- `GET /api/entities/{id}`
- `POST /api/copilot/query`
- `POST /api/actions/propose`
- `POST /api/actions/{id}/approve`
- `POST /api/actions/{id}/reject`
- `POST /api/evals/run`

Request context includes signed claims:
- `mission_ids`
- `clearance`
- `coalition`
- `roles`
- `compartments`

### 5.3 Event Backbone

Kafka topics:
- `intel.raw.events`
- `intel.normalized.events`
- `intel.enriched.events`
- `agent.recommendations`
- `operator.feedback`
- `eval.outcomes`
- `policy.decisions`

### 5.4 Retrieval + Search

Hybrid retrieval stack:
1. structured ontology query (high precision)
2. vector retrieval over reports/chunks
3. graph neighborhood expansion
4. rerank by confidence + recency + mission relevance

### 5.5 Model Router

Policy-aware routing examples:
- low-latency model for triage
- high-reasoning model for mission synthesis
- deterministic constrained output model for regulated artifacts

### 5.6 Observability + Evals

- OpenTelemetry traces with request/mission IDs
- model/tool call spans
- audit log append-only stream
- eval dashboards per mission/team/model route
- drift monitoring (input distribution + performance drift)

---

### 3) Ontology-aware query function

```python
from sqlalchemy import text

def fetch_case_graph(conn, case_id: str, max_depth: int = 2):
    sql = text("""
    WITH RECURSIVE g AS (
      SELECT e.entity_id, e.entity_type, e.canonical_name, 0 AS depth
      FROM ontology_entity e
      JOIN case_entity ce ON ce.entity_id = e.entity_id
      WHERE ce.case_id = :case_id
      UNION ALL
      SELECT e2.entity_id, e2.entity_type, e2.canonical_name, g.depth + 1
      FROM g
      JOIN ontology_relationship r ON r.src_entity_id = g.entity_id
      JOIN ontology_entity e2 ON e2.entity_id = r.dst_entity_id
      WHERE g.depth < :max_depth
    )
    SELECT * FROM g;
    """)
    return conn.execute(sql, {"case_id": case_id, "max_depth": max_depth}).mappings().all()
```

- **Zero Trust**: all calls authenticated/authorized; no network-location trust.
- **Need-to-know default deny**.
- **Compartment + coalition enforcement** at row/column/edge/action levels.
- **Policy-as-code** in gateway and tool runtime.
- **Prompt governance**: versioned prompts, test reports, approval signatures.
- **Model governance**: approved registry, intended-use constraints, fallback paths.
- **Immutable provenance**: append-only logs for data access, outputs, approvals, upgrades.

---

## 7) Code Examples (Python-First, Production-Oriented)

### 7.1 FastAPI Gateway + Policy Context

```python
# artemis/backend/recommendation_service.py
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from .policy import enforce_policy
from .router import route_model

app = FastAPI()

class RecommendationRequest(BaseModel):
    case_id: str
    mission_id: str
    operator_id: str

@app.post("/recommendations")
def generate_recommendation(req: RecommendationRequest):
    enforce_policy(actor=req.operator_id, action="read_case", resource=req.case_id)
    model = route_model(task="recommendation", mission_id=req.mission_id)
    # retrieve ontology context + evidence packets
    context = load_case_context(req.case_id, req.mission_id)
    draft = model.invoke(context)
    decision = enforce_policy(actor=req.operator_id, action="draft_recommendation", resource=req.case_id)
    return {"recommendation": draft, "policy": decision}
```

### 2) Event Handler (Streaming)

```python
# artemis/streaming/alert_consumer.py
from confluent_kafka import Consumer
from .workflow import start_workflow

consumer = Consumer({"bootstrap.servers": "kafka:9092", "group.id": "triage"})
consumer.subscribe(["intel.alerts"])

while True:
    msg = consumer.poll(1.0)
    if not msg or msg.error():
        continue
    event = parse_event(msg.value())
    start_workflow("triage_pipeline", payload=event)
```

### 3) Ontology-Driven Query

```sql
-- Find top-risk persons linked to a case within 2 hops, coalition-safe
WITH case_entities AS (
  SELECT entity_id FROM ontology.case_entity_link WHERE case_id = :case_id
),
neighbors AS (
  SELECT DISTINCT target_id AS person_id
  FROM ontology.edges
  WHERE source_id IN (SELECT entity_id FROM case_entities)
    AND edge_type IN ('ASSOCIATED_WITH','USES')
    AND hop_count <= 2
    AND coalition_tag = :coalition
)
SELECT p.person_id, p.name, p.risk_score, p.confidence_score
FROM ontology.person p
JOIN neighbors n ON n.person_id = p.person_id
ORDER BY p.risk_score DESC
LIMIT 25;
```

### 4) Policy-as-Code Gate (Rego)

```rego
package artemis.authz

default allow = false

allow {
  input.actor.clearance >= input.resource.classification
  input.actor.coalition == input.resource.coalition
  input.action == "read"
}

allow {
  input.action == "propose_action_package"
  input.actor.role == "analyst"
  not input.resource.operationally_significant
}
```

### 5) Workflow State Machine (Python)

```python
from enum import Enum

class State(str, Enum):
    TRIAGE="triage"
    ENRICH="enrich"
    CORRELATE="correlate"
    SUMMARIZE="summarize"
    RECOMMEND="recommend"
    POLICY_GATE="policy_gate"
    AWAIT_APPROVAL="await_approval"
    APPROVED="approved"
    REJECTED="rejected"

TRANSITIONS = {
    State.TRIAGE: State.ENRICH,
    State.ENRICH: State.CORRELATE,
    State.CORRELATE: State.SUMMARIZE,
    State.SUMMARIZE: State.RECOMMEND,
    State.RECOMMEND: State.POLICY_GATE,
    State.POLICY_GATE: State.AWAIT_APPROVAL,
}
```

### 6) Eval Pipeline (Python)

```python
# artemis/evals/offline_eval.py
from dataclasses import dataclass

@dataclass
class EvalResult:
    precision: float
    recall: float
    latency_ms_p95: int
    trust_accept_rate: float


def score(candidate, dataset) -> EvalResult:
    # evaluate recommendation correctness, evidence grounding, latency
    ...


def promote_if_safe(result: EvalResult) -> bool:
    return (
        result.precision >= 0.92 and
        result.recall >= 0.88 and
        result.latency_ms_p95 <= 1500 and
        result.trust_accept_rate >= 0.75
    )
```

---

## Security and Governance

- **Need-to-know enforcement**: row/column/entity/edge-level policy checks on every query.
- **Compartmentalization**: coalition tags, releasability labels, and cross-domain guards.
- **Zero trust**: workload identity, mTLS, signed service-to-service requests.
- **Immutable provenance**: append-only audit logs for data, model, prompt, and action changes.
- **Model governance**: versioned model registry with allowed-use scopes and deprecation schedule.
- **Prompt governance**: signed prompt artifacts, change tickets, mandatory review notes.
- **Operational governance**: action package execution requires role-based dual approval for high-impact classes.

---

## Scenario Walkthrough (Cinematic + Technical)

1. **Live event arrives**: a maritime anomaly signal enters `intel.alerts` stream with severity HIGH.
2. **Triage agent** scores novelty 0.91 and links to existing mission `M-447`.
3. **Enrichment agent** pulls related vessel, owner org, recent route deviations, sanctions metadata.
4. **Correlation agent** identifies pattern match to prior interdiction case with 0.83 confidence.
5. **Summarizer** drafts an intel note with explicit evidence references and confidence bands.
6. **Recommendation agent** proposes action package: escalate to commander + open coordinated case.
7. **Policy gate** checks coalition boundaries and legal basis; one redaction required is auto-applied.
8. **Human operator** approves escalation, rejects one sub-action as overbroad.
9. **Execution**: Gotham case is opened/updated; notification dispatches to mission team.
10. **Learning loop** records rejected sub-action rationale, updates eval dataset, and generates a candidate prompt tweak.
11. **Governance board** reviews candidate in weekly model/prompt review; approves canary to 10% traffic.
12. **Canary metrics** show +4.2% precision, -8% over-escalation, no policy regressions.
13. **Apollo promotion** advances candidate to production ring; prior version retained for instant rollback.

This is how ClearGlassInc Artemis improves continuously while remaining human-governed, auditable, and mission-safe.
