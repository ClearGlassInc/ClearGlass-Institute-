"""Command-line entrypoint for the Job Automation Agent stack.

Examples::

    # Score + shortlist today's roles from a JSON board, print the kits
    python3 -m job_agent.cli run \
        --jobs job_agent/examples/sample_jobs.json \
        --resume job_agent/examples/master_resume.md \
        --profile job_agent/examples/search_profile.json

    # Surface follow-ups that are due
    python3 -m job_agent.cli follow-ups --tracker tracker.json
"""

from __future__ import annotations

import argparse
import json
import sys

from job_agent.config import SearchProfile
from job_agent.pipeline import JobAutomationPipeline
from job_agent.sourcing import JSONFileSource


def _load_resume(path: str | None) -> str:
    if not path:
        return ""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _build_pipeline(args: argparse.Namespace) -> JobAutomationPipeline:
    profile = SearchProfile.load(args.profile) if args.profile else SearchProfile()
    sources = [JSONFileSource(args.jobs)] if args.jobs else []
    return JobAutomationPipeline(
        profile=profile,
        master_resume=_load_resume(args.resume),
        sources=sources,
    )


def _cmd_run(args: argparse.Namespace) -> int:
    pipeline = _build_pipeline(args)
    staged = pipeline.run_daily()
    print(f"== Engine: {pipeline.engine.name} ==")
    print(f"== Today's shortlist: {len(staged)} role(s) ==\n")
    for i, app in enumerate(staged, 1):
        print(f"{i}. [{app.score:>4.1f}] {app.job.title} @ {app.job.company}")
        for reason in app.reasons:
            print(f"      - {reason}")
        if app.kit:
            print(f"      outreach: {app.kit.outreach_message}")
        print(f"      apply:    {app.job.url}\n")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(
                [{**a.to_dict(), "kit": a.kit.to_dict() if a.kit else None} for a in staged],
                fh, indent=2,
            )
        print(f"Wrote {len(staged)} application kit(s) to {args.out}")
    return 0


def _cmd_follow_ups(args: argparse.Namespace) -> int:
    pipeline = _build_pipeline(args)
    # A real run would rehydrate the tracker; here we report the generator path.
    due = pipeline.follow_ups_due()
    if not due:
        print("No follow-ups due.")
        return 0
    for item in due:
        print(f"- {item['title']} @ {item['company']}\n  {item['message']}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="job_agent", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--jobs", help="Path to a JSON array of postings")
    common.add_argument("--resume", help="Path to the master resume (text/markdown)")
    common.add_argument("--profile", help="Path to a SearchProfile JSON file")

    run = sub.add_parser("run", parents=[common], help="Run the daily pipeline")
    run.add_argument("--out", help="Write the application kits to this JSON file")
    run.set_defaults(func=_cmd_run)

    fu = sub.add_parser("follow-ups", parents=[common], help="List due follow-ups")
    fu.add_argument("--tracker", help="Path to a saved tracker JSON file")
    fu.set_defaults(func=_cmd_follow_ups)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
