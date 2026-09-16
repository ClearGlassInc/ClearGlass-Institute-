# Engineering Guidelines

Engineering standards for the `Opal-Koboi` repository — the ClearGlassInc Artemis
enterprise platform. It is predominantly **Python** (including the `clearpulse`
triage & compliance pipeline and several agent services), with a **Node/npm**
platform package driven by CI and some **PowerShell** tooling. Rules below note
which stack they apply to.

## Principles

1. **Understand before changing.** Locate the subtree you are in — `clearpulse/`,
   `job_agent/`, `apps/`, `artemis/`, the root Node package — and read its tests
   and CI gate before editing.
2. **Smallest safe change.** Surgical fixes, no unrelated refactors or style churn.
3. **Keep the CI gate green.** `.github/workflows/ci.yml` runs `npm ci`,
   `npm test`, `npm run build`, `npm run dashboard`, and `npm run orchestrate`.
   Any change must leave all of those passing.

## clearpulse (triage & compliance pipeline)

`clearpulse` is deliberately layered: the **core engine** (ingestion, engine,
compliance, alerts, pipeline) depends only on the Python **standard library plus
PyYAML**, and its tests run on the stdlib alone. The FastAPI gateway adds the web
stack on top.

- Do **not** introduce third-party imports into the core engine — that would break
  the stdlib-only contract the tests rely on. Web-only dependencies stay in the
  gateway layer.
- The engine falls back to built-in defaults when tunable YAML rules are absent;
  preserve that graceful degradation.
- Run the tests:
  ```bash
  cd clearpulse
  pip install -r requirements.txt   # PyYAML (+ web stack for the gateway)
  python -m pytest tests/           # test_audit, test_clearpulse, test_graph, test_incidents
  ```

## Python (general)

- Target Python 3.11+, full type hints, `from __future__ import annotations`.
- Declare runtime dependencies in the relevant `requirements.txt`
  (`clearpulse/`, `job_agent/`, root). Never rely on an ambient install.
- Keep append-only audit trails auditable — do not drop logging or risk metadata
  from compliance/alert paths.

## Node / npm platform package

- `npm test`, `npm run build`, `npm run dashboard`, and `npm run orchestrate` are
  all CI-verified commands — keep them working. Node 22 is the CI runtime.
- The JS test suite (`test/opal-koboi.test.mjs`) must pass; add coverage for new
  platform behavior.

## PowerShell (`*.ps1`, `*.psm1`)

- Approved verbs for function names; `Set-StrictMode -Version Latest` and
  `$ErrorActionPreference = 'Stop'` at the top; typed, validated `param()` blocks.

## Security

- Never commit secrets, API keys, or tokens — use GitHub Actions secrets.
- Never log credentials or leak them in error messages; redact before surfacing.
- Validate and sanitize all external input; assume hostile input and fail closed.
- Workflows declare explicit least-privilege `permissions:` blocks (see `ci.yml`).

## Commits & pull requests

- Branch from `main`; lowercase, hyphen-separated, scoped branch names.
- One logical change per PR, clear title and description, CI green before merge.
  Open as a draft until CI passes.
- Every fix ships with a regression test in the appropriate suite.
