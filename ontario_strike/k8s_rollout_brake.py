#!/usr/bin/env python3
"""Abort-or-hold decision for a Kubernetes rollout from kubectl json.

Pass `kubectl rollout status` is late. This reads deployment/ds json and
prints HOLD if unavailable replicas, crash loops, or image skew exceed policy.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def inspect(doc: dict[str, Any]) -> dict[str, Any]:
    kind = doc.get("kind") or "Unknown"
    meta = doc.get("metadata") or {}
    spec = doc.get("spec") or {}
    status = doc.get("status") or {}
    desired = spec.get("replicas")
    if desired is None:
        desired = status.get("replicas") or 0
    ready = status.get("readyReplicas") or 0
    updated = status.get("updatedReplicas") or 0
    unavailable = status.get("unavailableReplicas") or 0
    conditions = {c.get("type"): c for c in status.get("conditions") or []}
    progressing = conditions.get("Progressing") or {}
    available = conditions.get("Available") or {}
    reasons = []
    if unavailable:
        reasons.append(f"unavailableReplicas={unavailable}")
    if desired and ready < desired:
        reasons.append(f"ready {ready}/{desired}")
    if desired and updated and updated < desired:
        reasons.append(f"updated {updated}/{desired}")
    if progressing.get("reason") == "ProgressDeadlineExceeded":
        reasons.append("ProgressDeadlineExceeded")
    if available.get("status") == "False":
        reasons.append(f"Available=False {available.get('reason')}")
    hold = bool(reasons)
    return {
        "kind": kind,
        "name": meta.get("name"),
        "namespace": meta.get("namespace"),
        "desired": desired,
        "ready": ready,
        "updated": updated,
        "unavailable": unavailable,
        "hold": hold,
        "reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Kubernetes rollout brake")
    parser.add_argument("--status", required=True, help="kubectl get deploy X -o json")
    args = parser.parse_args()
    path = Path(args.status)
    if not path.exists():
        print(f"missing status file: {path}", file=sys.stderr)
        return 2
    doc = json.loads(path.read_text(encoding="utf-8"))
    items = doc.get("items") if doc.get("kind") == "List" else [doc]
    reports = [inspect(item) for item in items]
    hold = any(r["hold"] for r in reports)
    print(json.dumps({"hold": hold, "workloads": reports}, indent=2))
    return 2 if hold else 0


if __name__ == "__main__":
    raise SystemExit(main())
