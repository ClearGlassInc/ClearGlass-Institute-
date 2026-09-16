# ClearGlass ARTEMIS Service Agent

A fixed-scope cybersecurity sales & qualification specialist for ClearGlass Inc.
(Burlington, Ontario). It qualifies leads against four defined offerings, speaks
in the verbatim service-page voice, enforces CASL / written-authorization
compliance, and prepares clean human handoffs.

## Files
| File | Purpose |
|------|---------|
| `system-prompt.md` | Canonical system prompt — load as the agent's instructions. |
| `knowledge-base.md` | The four offerings, pricing, CTAs, mission copy. **Has `<<FILL IN>>` placeholders.** |
| `few-shot-examples.md` | Tone/schema reference dialogues (draft templates). |

## Before going live (required)
The agent's #1 rule is **never invent services or pricing**. This scaffold ships
with placeholders so no fabricated numbers reach a prospect. Replace every
`<<FILL IN>>` / `<<PRICE>>` marker in `knowledge-base.md` (and the example files)
with the approved, verbatim service-page copy and pricing, then re-read the
guardrails section of `system-prompt.md`.

```bash
# Find everything that still needs real copy:
grep -rn "FILL IN\|<<PRICE>>" artemis/service-agent
```

## The four fixed-scope offerings
1. Microsoft 365 + Windows Hardening Sprint
2. Security Quick-Audit (default "start here" path)
3. PHIPA Readiness Assessment (Ontario health-sector — flag for human review)
4. Automation-as-a-Service (Human-in-the-Loop)

## Deployment options
- **Chat / direct:** paste `system-prompt.md` + `knowledge-base.md` +
  `few-shot-examples.md` as the system context for a Claude-powered assistant.
- **Ecosystem:** findings can feed the ClearGlass NEXUS dashboard / AgentOps
  platform for ongoing automation and monitoring.

## Compliance
- All outreach CASL-compliant.
- All engagements require **written authorization** before any access or testing.
- Ontario / Canadian context only (PHIPA, Ontario health-sector, Burlington ops).
