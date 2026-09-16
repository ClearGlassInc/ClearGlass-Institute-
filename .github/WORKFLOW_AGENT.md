# GitHub Workflow Repair & Execution Agent — Repository Policy

This is the standing prompt and policy for any coding agent, agentic CI job, or
repo assistant that inspects, fixes, runs, or maintains the GitHub Actions
workflows in this repository (`.github/workflows/`).

## Mission

Inspect, fix, validate, and maintain all GitHub workflows and related automation
with minimal human intervention while preserving **security, reliability, and
traceability**. Never weaken repository security to "make it work."

## Operating rules

1. Before changing anything, scan every file in `.github/workflows/` and any
   reusable workflows or composite actions they call.
2. Identify: YAML/parse errors, invalid expressions, missing/over-broad
   permissions, deprecated or unpinned actions, dangerous triggers, and likely
   runtime failures (missing files, bad paths, unsupported runner assumptions).
3. Prefer reusable workflows, explicit per-job permissions, and pinned versions
   over ad hoc scripts.
4. Never use mutable action references like `@master` or `@latest`. Pin to a
   stable tag or, preferably, an immutable commit SHA.
5. Treat all external input — PR data, issue bodies, artifacts, uploaded files —
   as untrusted. Validate untrusted strings before using them in `run:` shells
   or `${{ }}` expressions.
6. Avoid broad `pull_request_target` usage unless explicitly required and
   secured. Use GitHub Secrets or OIDC, never hardcoded credentials. Never print
   secrets to logs.
7. Keep diffs minimal and explain every behavior change.

## Repair priority order

1. YAML / parse errors
2. Broken action references
3. Permission failures
4. Missing files or commands
5. Dependency / cache inefficiencies
6. Security weaknesses
7. Maintainability improvements

## Security baseline (enforced)

- **Read-only default token.** Every workflow declares top-level
  `permissions: contents: read`; jobs elevate only the exact scope they need
  (e.g. `repo-assistant-bot.yml` → `issues: write`).
- **Least-privilege publishing.** `npm-publish.yml` publishes to
  `registry.npmjs.org` via the `NPM_TOKEN` secret and therefore does **not**
  request the GitHub `packages: write` scope. Re-add it to the `publish-npm`
  job only if the target is ever switched to GitHub Packages.
- **Safe triggers.** No `pull_request_target`; the bot workflow runs on
  `issues: opened` and the publish workflow on `release: created` /
  `workflow_dispatch`.
- **Concurrency guards.** Long-running workflows set a `concurrency` group with
  `cancel-in-progress: true`.

## Required output format (every run)

Report: **Files inspected → Problems found → Fixes applied → Validation
performed → Remaining risks → PR summary (if changes were made)**.

## Implemented automation

- **`.github/scripts/audit_workflows.py`** — the deterministic, read-only
  auditor. Enforces this baseline (top-level permissions, no mutable refs,
  third-party actions pinned to SHA) and exits non-zero on any ERROR. Run it
  locally or in CI: `python3 .github/scripts/audit_workflows.py`.
- **`.github/workflows/workflow-repair-agent.yml`** — the agent workflow:
  - `audit` job: runs the auditor on a weekly schedule **and** every dispatch.
  - `repair` job: gated behind manual dispatch + the `autofix` input + the
    presence of `ANTHROPIC_API_KEY`. Runs `anthropics/claude-code-action`
    against this policy, then opens a PR via `peter-evans/create-pull-request`.
    Both third-party actions are pinned to commit SHAs. It never runs
    unattended and never blocks scheduled CI.

To enable autofix: add the `ANTHROPIC_API_KEY` repository secret, then run the
workflow from the Actions tab with **autofix = true**.

## Commit / PR conventions

- Commit message for workflow repairs: `fix(ci): repair GitHub workflows and validation`
- Open a PR only when the human asks; explain every change and include rollback
  notes (the previous file content / reverting the PR is the rollback).

## Known remaining risk (tracked)

- **First-party action tags.** The repo's `actions/*` references (checkout,
  setup-node, setup-python, github-script) use major-version tags (`@v5`,
  `@v7`), which are mutable but first-party and widely trusted. Third-party
  actions are pinned to commit SHAs. Hardening the first-party tags to SHAs is
  optional and must use **verified** SHAs for the intended release — pinning to
  an unverified SHA would break the workflow.

## Validating workflow changes locally

```bash
# Structural YAML + permissions audit (requires PyYAML).
python3 - <<'PY'
import glob, yaml
for p in sorted(glob.glob(".github/workflows/*.yml")):
    d = yaml.safe_load(open(p))
    print(p, "perms:", d.get("permissions"))
PY
```
