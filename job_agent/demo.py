"""Self-contained Job Automation Agent demo - the full daily flow.

Run with::

    python3 -m job_agent.demo

Requires no API key or network: it drives the in-process pipeline over a small
built-in board, prints the scored shortlist with tailored outreach, simulates
applying + a follow-up coming due, and prints the Opportunity Intelligence
report.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from job_agent.config import SearchProfile
from job_agent.models import ApplicationStatus, JobPosting
from job_agent.pipeline import JobAutomationPipeline
from job_agent.sourcing import StaticSource


_RESUME = """\
- Closed $40M+ in strategic partnerships across fintech and crypto.
- Built BD and operations teams from scratch at two early-stage startups.
- Led go-to-market for a stablecoin payments product through licensing.
"""


def _sample_board() -> list[JobPosting]:
    today = date(2026, 6, 15)
    return [
        JobPosting(
            title="Head of Business Development",
            company="Figure",
            url="https://boards.greenhouse.io/figure/jobs/1",
            description="Own partnerships and revenue for our crypto lending platform. "
                        "Lead go-to-market, licensing, and strategic deals.",
            location="Remote (US)", remote=True,
            salary_min=160_000, salary_max=210_000,
            source="greenhouse", posted_date=today, contact_name="Dana",
        ),
        JobPosting(
            title="Director of Strategy & Operations",
            company="Block",
            url="https://block.xyz/careers/2",
            description="Drive operations and strategy across our fintech and bitcoin "
                        "business units. Partnerships experience a plus.",
            location="Remote", remote=True,
            salary_min=150_000, salary_max=190_000,
            source="cryptojobslist", posted_date=today - timedelta(days=1),
        ),
        JobPosting(
            title="Partnerships Lead, Web3",
            company="Alpaca",
            url="https://alpaca.markets/jobs/3",
            description="Build the web3 partner ecosystem. GTM, BD, and revenue ownership.",
            location="Hybrid - NYC", remote=False,
            salary_min=130_000, salary_max=170_000,
            source="remote100k", posted_date=today - timedelta(days=3),
        ),
        JobPosting(  # below floor + off-target: should be filtered out
            title="Junior Marketing Coordinator",
            company="Acme",
            url="https://acme.com/jobs/4",
            description="Social media and email marketing for a retail brand.",
            location="On-site", remote=False,
            salary_min=55_000, salary_max=65_000,
            source="indeed", posted_date=today,
        ),
    ]


def main() -> None:
    profile = SearchProfile(candidate_name="Dezzy")
    pipeline = JobAutomationPipeline(
        profile=profile,
        master_resume=_RESUME,
        sources=[StaticSource(_sample_board(), name="demo-board")],
    )

    print("== AGENT 1+2+3: source -> score -> personalise ==")
    staged = pipeline.run_daily(today=date(2026, 6, 15))
    for i, app in enumerate(staged, 1):
        print(f"\n{i}. [{app.score:>4.1f}/10] {app.job.title} @ {app.job.company}")
        for reason in app.reasons:
            print(f"     - {reason}")
        print(f"     outreach: {app.kit.outreach_message}")
        print(f"     bullet:   {app.kit.resume_bullets[0]}")

    print("\n== AGENT 4: apply + arm follow-up clock ==")
    top = staged[0]
    pipeline.tracking.mark_applied(top.id, on=date(2026, 6, 10))
    print(f"   Applied to {top.job.company}; follow-up armed for {pipeline.tracking.get(top.id).follow_up_date}")

    print("\n== follow-ups due as of 2026-06-15 ==")
    for item in pipeline.follow_ups_due(today=date(2026, 6, 15)):
        print(f"   {item['company']}: {item['message']}")

    print("\n== Opportunity Intelligence Layer ==")
    # Seed a couple of outcomes so the analytics have signal.
    pipeline.tracking.set_status(top.id, ApplicationStatus.INTERVIEW)
    if len(staged) > 1:
        pipeline.tracking.mark_applied(staged[1].id, on=date(2026, 6, 12))
        pipeline.tracking.set_status(staged[1].id, ApplicationStatus.REJECTED)
    print(json.dumps(pipeline.intelligence_report(), indent=2))


if __name__ == "__main__":
    main()
