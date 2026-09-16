# Job Automation Agent Stack

A four-agent pipeline that **sources, scores, personalises, and tracks**
applications to high-paying roles (e.g. BD / strategy / operations / partnerships
in crypto, fintech, and web3 at $100k+). It runs end-to-end with the Python
standard library — **no API key and no network required** — and transparently
upgrades to Claude-tailored copy when `ANTHROPIC_API_KEY` is present.

```
Agent 1: Sourcing  ──▶  Agent 2: Scoring  ──▶  Agent 3: Personalization  ──▶  Agent 4: Apply + Track
 find jobs daily        filter + score 1-10      tailor resume + outreach        log, follow up, learn
```

## Quick start

```bash
# Zero-config end-to-end demo (built-in sample board, no key needed)
python3 -m job_agent.demo

# Run the daily pipeline over your own board + resume + profile
python3 -m job_agent.cli run \
    --jobs   job_agent/examples/sample_jobs.json \
    --resume job_agent/examples/master_resume.md \
    --profile job_agent/examples/search_profile.json \
    --out    today_kits.json

# Tests
python3 -m unittest discover -s job_agent/tests
```

## The four agents

| # | Module | Responsibility |
|---|--------|----------------|
| 1 | `job_agent/sourcing.py` | Pull postings from pluggable `JobSource` adapters, parse salary, dedup by fingerprint. |
| 2 | `job_agent/scoring.py` | Score each role **1–10** with an explainable component breakdown, then apply the score floor + `$100k` salary gate and return the day's top-N. |
| 3 | `job_agent/personalization.py` | Generate tailored resume bullets, a cover note, and a 1–2 sentence outreach line per role. |
| 4 | `job_agent/tracking.py` | Stage applications, arm the follow-up clock, generate follow-up copy, and mirror rows to an external sink. |
| ★ | `job_agent/intelligence.py` | **Opportunity Intelligence Layer**: response rate by function/salary band, fastest-responding companies, recommendations. |

`job_agent/pipeline.py` wires them together; `job_agent/config.py` holds the
`SearchProfile` (who you are + what you want + scoring weights).

## How scoring works (transparent, tunable)

Each role earns points across six bands defined in `ScoringWeights`, normalised
to a 0–10 score. Title keyword hits count double versus body hits; salary clears
or scales toward the floor; freshness decays over a two-week window. Every score
ships with its `components` dict and three plain-English `reasons`, so nothing is
a black box. Tune the weights in your `search_profile.json`.

## Plugging in real sources

`JSONFileSource` and `StaticSource` ship in the box. A production adapter just
implements `fetch() -> Iterable[JobPosting]`:

```python
class GreenhouseSource:
    name = "greenhouse"
    def __init__(self, board): self.board = board
    def fetch(self):
        # GET https://boards-api.greenhouse.io/v1/boards/<board>/jobs?content=true
        # yield posting_from_dict({...}, source="greenhouse")
        ...
```

Wire any mix into the pipeline: Greenhouse boards (Figure, Block, Alpaca),
Remote100K / CryptoJobsList RSS, an Apify actor, or a PhantomBuster LinkedIn
export dropped as JSON.

## The Claude personalization upgrade

Set `ANTHROPIC_API_KEY` and the pipeline auto-selects `ClaudeEngine`
(`pip install anthropic`). The Personalization Agent then produces genuinely
tailored bullets/cover/outreach instead of templates. Swap providers by
implementing the tiny `LLMEngine.complete` protocol in `job_agent/llm.py`.

---

## Deploying as a scheduled stack (no-code / low-code map)

The Python package is the engine. To run it unattended on the "7 AM" cadence
from the brief, here is the recommended wiring.

### Airtable base — `Applications` table

| Field | Type | Source |
|-------|------|--------|
| Title | Single line | `JobPosting.title` |
| Company | Single line | `JobPosting.company` |
| URL | URL | `JobPosting.url` |
| Salary Range | Single line | `salary_min`–`salary_max` |
| Score | Number | `ScoredJob.score` |
| Match Reasons | Long text | `ScoredJob.reasons` |
| Status | Single select | `Sourced / Queued / Applied / Followed Up / Interview / Offer / Rejected / Skipped` |
| Applied Date | Date | `Application.applied_date` |
| Follow-up Date | Date | `Application.follow_up_date` |
| Contact | Single line | `Application.contact_name` |
| Resume Bullets | Long text | `ApplicationKit.resume_bullets` |
| Outreach | Long text | `ApplicationKit.outreach_message` |

`Application.to_dict()` already emits these field names — point a `TrackerSink`
at the Airtable API (or use `JSONTrackerSink` to stage rows for a Zapier import).

### Zapier / Make workflow map

```
1. Schedule (daily 7:00)            ──▶  Run pipeline  (Code step / webhook to the CLI)
2. Pipeline emits today_kits.json   ──▶  Create/Update Airtable rows (Status=Queued)
3. You review in Airtable (5–10 min)──▶  Flip Status to "Applied"
4. Airtable "Applied" trigger       ──▶  Google Calendar reminder @ Follow-up Date
5. Schedule (daily 7:05)            ──▶  follow_ups_due()  ──▶  draft LinkedIn/email nudges
```

### Prompt templates (used by `ClaudeEngine`, editable in `llm.py`)

- **Resume tailoring** — "Rewrite my resume bullets to match this job. Focus on
  BD wins (revenue, partnerships), operations + strategy, crypto/fintech
  relevance. Concise and results-driven."
- **Outreach** — "Write a short LinkedIn message to the hiring manager. Tone:
  confident, entrepreneurial, direct. 1–2 sentences max."
- **Scoring** — "Score this job 1–10 for fit (BD, operations, licensing,
  crypto/fintech relevance, $100k+ seniority, entrepreneurship). Return score +
  3 bullet reasons."

## A note on responsible automation

Application submission here is **assisted, not silent-auto**: the pipeline stages
a reviewed shortlist with ready collateral and the apply URL for a
human-in-the-loop click. That keeps you compliant with job-board and LinkedIn
terms of service (which restrict unattended bulk auto-apply / scraping) and keeps
a human accountable for what gets sent under your name.
