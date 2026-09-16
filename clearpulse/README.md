# ClearPulse — Triage & Compliance Pipeline

ClearPulse traces a single patient encounter from raw signal (FHIR encounter
bundles, ADT/staff access logs, billing claims) to a correlated, scored, and
fully attributable alert on the NEXUS-Med dashboard. Every stage carries an
immutable **ClearPulse Trace ID** so any risk score can be unpacked back to the
facts that produced it.

This package is a **scaffold**: the core logic is real and unit-tested, while
the distributed substrate (Redis streams, RocksDB window state, a PostgreSQL
source-of-truth, the Parquet ledger, and the React dashboard) is represented by
clean in-process seams ready to be wired to those services.

## Layout

| Module | Layer | Responsibility |
| --- | --- | --- |
| `ingestion/parser.py` | Data | Validate/normalise FHIR bundles & access logs → `ObservableFact` / `AccessEvent`, stamped with a Trace ID. |
| `engine/window.py` | Logic | Sliding-window (15 min) per-patient state for temporal correlation. |
| `engine/risk.py` | Logic | `overlap_ratio` + `RiskScorer` → an explainable `RiskEnvelope`. |
| `engine/access.py` | Logic | Rolling distinct-patient access counts and Z-score spike detection. |
| `compliance/scanner.py` | Security | At-rest PHI/PII regex scan with masked findings + severity. |
| `alerts/router.py` | Routing | Dedup + correlation (access spike ↔ billing anomaly = compromised-account hypothesis). |
| `pipeline.py` | Orchestration | Wires the stages into one reference path. |
| `backend/app.py` | Orchestration | FastAPI ingress gateway (mirrors `artemis/backend/app.py`). |
| `config/risk_rules.yaml` | Config | Tunable scoring weights/thresholds (no redeploy needed). |

## Risk model

Weights live in `config/risk_rules.yaml` (engine falls back to identical
built-in defaults if PyYAML or the file is missing):

| Factor | Max points |
| --- | --- |
| Temporal billing overlap (ratio > 0.6) | 40 |
| Unusual procedure mix | 20 |
| Access volume spike (scaled by Z-score) | 50 |
| High-risk / VIP patient | 10 |
| Off-hours activity | 10 |
| **Total cap** | **100** |

Scores map to dashboard bands: `low` ≤ 25, `medium` 26–69, `high` ≥ 70.

## Running

```bash
# Core engine + tests need only the standard library (+ PyYAML for rules).
python3 -m unittest clearpulse.tests.test_clearpulse -v

# A quick end-to-end demo (no external services required).
python3 -m clearpulse.demo

# The FastAPI gateway (requires the web extras in requirements.txt).
pip install -r clearpulse/requirements.txt
uvicorn clearpulse.backend.app:app --reload
```

## Known extensions (intentionally out of scope for the scaffold)

- Retroactive re-scoring of an earlier claim when a later overlap arrives
  (the design doc's `abc123` → re-emit a new envelope).
- Swapping the exact rolling access set for counting Bloom filters / HyperLogLog
  sketches at production scale.
- Backing the window with RocksDB and the alert store with PostgreSQL +
  WebSocket fan-out to the dashboard.
