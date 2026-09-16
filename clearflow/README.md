# ClearFlow — AI Automation Core Workflow Engine

ClearFlow is ClearGlassInc's daily operating model encoded as a workflow engine.
It exists to enforce **one discipline**:

> Advance exactly **ONE keystone outcome** today (the day's P0), and let it
> *unlock* every other domain behind it.

The bot ingests a **Strategic Priority Matrix**, the morning **pledge** (three
commitments), and the **Critical Intelligence Brief**, then drives the keystone
to `DONE` — the single event that opens the rest of the day.

This package is a **scaffold** in the same spirit as the sibling `clearpulse`:
the core logic is real and unit-tested, while the distributed substrate (a
scheduler daemon, a persistence store, a notifier fan-out, a dashboard) is
represented by clean in-process seams ready to be wired to those services.

## The single-outcome contract

The gate is the whole point. Every non-keystone item starts `LOCKED` and depends
on the keystone. The engine refuses to start another domain while the keystone
is open; completing the keystone (with evidence against its success metric)
reconciles the gate and flips every now-satisfied item `LOCKED → PENDING`.

```
P0  AI Automation   Code core workflow module     ← keystone (the one thing)
P1  Cybersecurity   Review key vulnerabilities     LOCKED ──┐ unlock when
P2  Personal Brand  LinkedIn post on AI trend       LOCKED ──┘ keystone lands
```

> Fittingly, today's keystone *is this module* — "Code core workflow module,
> functional and tested." Running the test suite green is the success metric.

## Layout

| Module | Layer | Responsibility |
| --- | --- | --- |
| `models.py` | Data | `WorkItem`, `Pledge`, `IntelSignal`, `TimeBlock`, `Priority`/`Status`, Trace IDs. |
| `matrix.py` | Data | Build/seed the Strategic Priority Matrix from rows. |
| `engine/gating.py` | Logic | `DomainGatekeeper` — wires the keystone gate, reconciles unlocks. |
| `engine/scheduler.py` | Logic | `BlockScheduler` — resolves *what should I do right now?* |
| `engine/pledge.py` | Logic | `PledgeLedger` — three daily commitments + next-day review. |
| `engine/graph.py` | Logic | `DependencyGraph` — topological order, cycle detection, **critical path** by effort. |
| `intel/brief.py` | Intel | `IntelRouter` — routes brief headlines to the domain they inform. |
| `events.py` | Bus | `EventBus` — typed, fault-isolating publish/subscribe + audit log. |
| `notify.py` | Seam | `Notifier` (console / collecting / webhook) — events → outbound signals. |
| `store.py` | Persistence | `HistoryStore` — durable day records, **streaks**, pledge **carryover**. |
| `runner.py` | Async | `DayRunner` — drive the matrix across a virtual `Clock` with `asyncio`. |
| `workflow.py` | Orchestration | `AutomationWorkflow` — binds the stages, emits events, enforces the contract. |
| `bot.py` | Front end | `DailyOutcomeBot` — morning briefing, live status, close-out. |
| `__main__.py` | CLI | `python3 -m clearflow <briefing\|status\|plan\|land\|run\|history>`. |
| `backend/app.py` | Gateway | Optional FastAPI surface (drive the day over HTTP). |

## Advanced subsystems

- **Event bus** (`events.py`) — every transition (`item.started`,
  `keystone.landed`, `domain.unlocked`, …) is published as a typed `Event`.
  Subscriber errors are isolated and captured on `bus.dead_letters`; the log
  doubles as an ordered audit trail. The keystone-landed event is emitted
  *before* the domain-unlock events so subscribers see cause then effect.
- **Dependency graph & critical path** (`engine/graph.py`) — generalises the
  gate to an arbitrary DAG: Kahn topological ordering (keystone-first tie-break),
  cycle detection with a recovered cycle for the error, and the longest
  effort-weighted chain — the day's irreducible lower bound.
- **Notifier seam** (`notify.py`) — `WebhookNotifier` POSTs event JSON via
  stdlib `urllib` (Slack-incoming-webhook shape); the natural wiring point for
  the Zapier / Gmail / Calendar MCP servers in this workspace.
- **Durable history** (`store.py`) — atomic JSON (`os.replace`) day records,
  consecutive keystone-landed **streaks**, and **carryover** of unkept pledges,
  so "Yesterday's Pledge Review" reads real data instead of a stub.
- **Async runner** (`runner.py`) — a virtual `Clock` advances focus tick by tick;
  `simulate_day` drives an entire accelerated day unattended, still strictly
  through the single-outcome gate.

## Running

```bash
# Core engine + ALL tests need only the standard library.
python3 -m unittest clearflow.tests.test_clearflow clearflow.tests.test_advanced -v

# The seeded single-outcome day, start to finish (no external services).
python3 -m clearflow.bot

# A narrated demo that proves the gate (other domains refuse to start early).
python3 -m clearflow.demo

# The CLI front end.
python3 -m clearflow briefing          # morning briefing
python3 -m clearflow plan              # execution order + critical path
python3 -m clearflow run               # simulate the whole day (async)
python3 -m clearflow land "shipped & tested"
python3 -m clearflow history --store .clearflow_history.json --record

# Optional HTTP gateway (needs the web extras).
pip install -r clearflow/requirements.txt
uvicorn clearflow.backend.app:app --reload
```

## Driving it from code

```python
from clearflow.bot import DailyOutcomeBot

bot = DailyOutcomeBot.from_today()
print(bot.morning_briefing())

# Land the keystone with evidence; everything gated behind it unlocks.
unlocked = bot.land_keystone("module functional, tested")
print(bot.status_line())
```

Or bring your own matrix:

```python
from clearflow.matrix import build_matrix
from clearflow.workflow import AutomationWorkflow

wf = AutomationWorkflow(build_matrix([
    {"priority": "P0", "domain": "AI Automation",
     "action": "Code core workflow module", "time_block": "8-10 AM",
     "success_metric": "Module functional, tested"},
    {"priority": "P1", "domain": "Cybersecurity",
     "action": "Review key vulnerabilities", "time_block": "10:30-11:30 AM",
     "success_metric": "Report with 3 fixes"},
]))
wf.start(wf.keystone)
wf.complete(wf.keystone, "tested and shipped")   # unlocks the P1
```

## Known extensions (intentionally out of scope for the scaffold)

- Bridging the in-process `EventBus` to Redis pub/sub (or a broker) and the
  `WebhookNotifier` to a live Slack/Zapier endpoint for real fan-out.
- A FastAPI gateway (`clearflow.backend`) mirroring `clearpulse.backend` so the
  bot can be driven over HTTP from a dashboard.
- Richer intel routing (embeddings instead of keyword hits) and auto-attaching
  signals to the matrix rows they inform.
