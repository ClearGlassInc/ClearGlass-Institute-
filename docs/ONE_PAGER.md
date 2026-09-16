# ClearGlass — Operational AI, Audited by Design

**One platform, two hardened products.** ClearGlass turns autonomous systems into
*accountable* ones: every decision is constrained, traceable, and defensible.

---

## What it is

| Product | What it does | Proof it works |
| --- | --- | --- |
| **ClearFlow** — AI automation engine | Drives **one keystone outcome per day** and gates every other workstream behind it. Critical-path planning, dependency gating, async execution, event bus, durable history. | 44 automated tests green · runs a full day to 100% completion unattended |
| **ClearPulse** — forensic compliance pipeline | Real-time triage of clinical/operational events → risk-scored, correlated, sealed alerts. Tamper-evident audit ledger + incident graph. | 46 tests green · live run flagged billing fraud, an insider snoop (3σ), and unencrypted PHI in milliseconds |
| **Control Surface v3.0** | Operator UI: command palette, live status telemetry (NOMINAL/SYNCING/DEGRADED/FAILURE), systems drawer. Keyboard-first, ARIA-correct. | Zero-dependency, ships with the portfolio |

## Why it's different

- **Constraint is the feature.** One outcome at a time beats a 14-item backlog that never ships.
- **Every action is auditable.** Hash-chained ledgers mean any decision reconstructs back to the event that caused it — the difference between "we think" and "we can prove."
- **Standard-library core.** The engines run with no heavyweight runtime; the web/API layers are optional seams, not lock-in.

## Who it's for

Regulated operators (healthcare, defense, fintech) and platform teams running
autonomous agents who need oversight, not just output.

---

## Pricing (proposed starting tiers — adjust to your market)

| Tier | For | Price (suggested) | Includes |
| --- | --- | --- | --- |
| **Open Core** | Builders, evaluation | Free (MIT, on npm) | ClearFlow + ClearPulse engines, CLI, docs |
| **Team** | Single ops team | **$490 / mo** | Hosted API gateway, Control Surface, webhook notifiers, email support |
| **Enterprise** | Regulated org | **From $3,500 / mo** | SSO, on-prem/VPC deploy, audit-ledger retention SLAs, the Workflow Repair Agent, priority support |
| **Design partner** | First 3 logos | Custom | Co-built integration + case study in exchange for a reference |

> Pricing is a starting proposal, not a commitment — anchored to comparable
> compliance-automation tooling. Validate against 3–5 customer conversations
> before locking it in.

## Get it

- **Install:** `npm i @clearglassinc/opal-koboi`
- **Source:** https://github.com/ClearGlassInc/Opal-Koboi
- **Live console:** https://clearglassinc.github.io/opal/
