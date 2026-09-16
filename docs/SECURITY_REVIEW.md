# Cybersecurity Review — CI/CD & Supply Chain (P1)

**Scope:** GitHub Actions workflows and release/supply-chain posture for
`ClearGlassInc/Opal-Koboi`.
**Date:** 2026-06-15 · **Reviewer:** ClearGlass Workflow Repair & Execution Agent
**Method:** deterministic auditor (`.github/scripts/audit_workflows.py`) + manual
review of every file in `.github/workflows/`, triggers, token scope, secret
handling, and third-party action provenance.

---

## Summary

Five workflows reviewed. **Three concrete vulnerabilities** were found and
fixed; the fixes are merged to `main`. The repository now enforces a
least-privilege, pinned, auditable CI baseline, with an automated guard so the
posture cannot silently regress.

| # | Severity | Finding | Status |
| - | -------- | ------- | ------ |
| 1 | High | Over-privileged default `GITHUB_TOKEN` (no top-level `permissions`) | ✅ Fixed |
| 2 | Medium | Unused/over-broad `packages: write` scope on the publish workflow | ✅ Fixed |
| 3 | Medium | Unpinned third-party actions + no drift enforcement | ✅ Fixed |

---

## Fix 1 — Lock the default token to read-only (High)

**Vulnerability.** `repo-assistant-bot.yml` declared no top-level `permissions`
block, so its `GITHUB_TOKEN` inherited the repository default — potentially
**write-all**. A workflow triggered by `issues: opened` (attacker-influenceable
input) running with broad write scope is a privilege-escalation foothold.

**Fix.** Added a top-level read-only default and scoped the elevated permission
to only the job that needs it:

```yaml
permissions:
  contents: read          # top-level default for the whole workflow
jobs:
  greet-and-label:
    permissions:
      contents: read
      issues: write        # the only elevation, on the only job that needs it
```

**Verification.** Auditor asserts a top-level `permissions` block exists on every
workflow (ERROR otherwise).

## Fix 2 — Drop the unused publish scope (Medium)

**Vulnerability.** `npm-publish.yml` granted `packages: write` at the top level
(both jobs). Publishing targeted `registry.npmjs.org` via an `NPM_TOKEN`, so the
GitHub `packages` scope was **unused** — a standing over-grant that widened the
blast radius of any compromised step.

**Fix.** Removed the blanket grant; default to `contents: read` and elevate
per-job only where a publish actually occurs. (When the publish target later
moved to GitHub Packages, `packages: write` was added back to the
`publish-npm` job *only*, with the top level still read-only.)

**Verification.** Manual diff + auditor; least privilege confirmed per job.

## Fix 3 — Pin third-party actions and enforce it (Medium)

**Vulnerability.** Supply-chain risk: a third-party action referenced by a
mutable tag (`@v1`, or worse `@master`) can be repointed to malicious code after
review. There was also no mechanism preventing future drift.

**Fix.**
- All **third-party** actions are pinned to a full 40-hex commit SHA
  (e.g. `peter-evans/create-pull-request@5f6978f…`,
  `anthropics/claude-code-action@787c5a0…`).
- Added `.github/scripts/audit_workflows.py`: fails CI on any missing top-level
  `permissions`, any mutable ref (`@master`/`@main`/`@latest`), or any
  third-party action not pinned to a SHA.
- Added `.github/workflows/workflow-repair-agent.yml`: runs the auditor weekly
  and on dispatch; an opt-in, secret-gated repair job opens fix PRs.

**Verification.** `python3 .github/scripts/audit_workflows.py` → **0 errors**
across all 5 workflows.

---

## Additional controls confirmed (no change required)

- **Secret hygiene.** No secret is ever echoed. The publish path uses a guard
  that checks *presence* of a credential via a boolean (`secrets.X != ''`) and
  skips cleanly rather than failing or leaking.
- **Trigger safety.** No `pull_request_target`; the bot runs on `issues`,
  publishing on `release` / gated `workflow_dispatch`.
- **Concurrency.** Long-running workflows set `concurrency` with
  `cancel-in-progress: true` to avoid overlapping privileged runs.

## Residual risks (tracked)

- **First-party `actions/*` tags.** `actions/checkout`, `setup-node`,
  `setup-python`, `github-script` use major-version tags (`@v5`/`@v7`) — mutable
  but first-party and widely trusted. SHA-pinning them is optional hardening and
  must use **verified** SHAs (an unverified pin would break CI).
- **Published package visibility.** The package ships to GitHub Packages and is
  **private** (follows the private repo). Moving to public npmjs.org requires an
  `NPM_TOKEN` secret — a deliberate, owner-gated decision.

## How to re-run this review

```bash
python3 .github/scripts/audit_workflows.py     # deterministic, exits non-zero on any ERROR
```
