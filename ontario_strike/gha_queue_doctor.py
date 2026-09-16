#!/usr/bin/env python3
"""Diagnose GitHub Actions queue delay and missing concurrency.

Input is a JSON list of workflow run objects (gh run list --json
databaseId,name,status,conclusion,event,createdAt,updatedAt,headBranch
or Actions API). No token is required if you pass an export.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def duration_s(run: dict[str, Any]) -> float | None:
    start = parse_dt(run.get("createdAt") or run.get("created_at"))
    end = parse_dt(run.get("updatedAt") or run.get("updated_at"))
    if not start or not end:
        return None
    return max(0.0, (end - start).total_seconds())


def analyze(runs: list[dict[str, Any]]) -> dict[str, Any]:
    names = Counter()
    fail = Counter()
    queuedish = 0
    long_runs = []
    branch_load = Counter()
    missing_conc_hint = Counter()
    durs = []
    for run in runs:
        name = run.get("name") or run.get("workflowName") or "unknown"
        names[name] += 1
        conclusion = (run.get("conclusion") or "").lower()
        status = (run.get("status") or "").lower()
        if conclusion in {"failure", "timed_out", "cancelled"}:
            fail[name] += 1
        if status in {"queued", "waiting", "pending"}:
            queuedish += 1
        branch = run.get("headBranch") or run.get("head_branch") or ""
        if branch:
            branch_load[branch] += 1
        dur = duration_s(run)
        if dur is not None:
            durs.append(dur)
            if dur > 1800:
                long_runs.append({"name": name, "seconds": int(dur), "branch": branch})
        if run.get("event") in {"push", "pull_request"}:
            missing_conc_hint[name] += 1
    p95 = sorted(durs)[int(0.95 * (len(durs) - 1))] if durs else 0
    recs = []
    if queuedish:
        recs.append("queued/waiting runs present — add larger runners or concurrency cancel-in-progress")
    if p95 > 1200:
        recs.append(f"p95 wall time {int(p95)}s — split jobs, cache deps, drop duplicate workflow files")
    hot = [n for n, c in missing_conc_hint.most_common(5) if c >= 8]
    if hot:
        recs.append(
            "add concurrency groups for: "
            + ", ".join(hot)
            + "  example: concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }"
        )
    flake_rate = []
    for name, total in names.items():
        if total >= 5 and fail[name] / total >= 0.2:
            flake_rate.append({"workflow": name, "fail_ratio": round(fail[name] / total, 2), "n": total})
    if flake_rate:
        recs.append("quarantine flaky workflows before adding more jobs")
    return {
        "runs": len(runs),
        "queued_or_waiting": queuedish,
        "p95_seconds": int(p95),
        "long_runs": sorted(long_runs, key=lambda x: x["seconds"], reverse=True)[:10],
        "flaky": flake_rate,
        "top_workflows": names.most_common(8),
        "recommendations": recs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="GitHub Actions queue / flake doctor")
    parser.add_argument("--log", required=True, help="JSON file of workflow runs")
    args = parser.parse_args()
    path = Path(args.log)
    if not path.exists():
        print(f"missing log file: {path}", file=sys.stderr)
        return 2
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "workflow_runs" in raw:
        runs = raw["workflow_runs"]
    elif isinstance(raw, list):
        runs = raw
    else:
        print("expected list or {workflow_runs: [...]}", file=sys.stderr)
        return 2
    result = analyze(runs)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
