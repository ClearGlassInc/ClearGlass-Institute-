#!/usr/bin/env python3
"""Fail a Terraform plan that will blow time, cost, or blast radius.

Reads `terraform show -json` output. No cloud credentials required.
Exit 2 = block the pipeline. Exit 0 = plan is inside policy.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DESTROY_MAX = 10
CREATE_MAX = 80
UNKNOWN_MAX = 5
COST_TOUCH_RESOURCES = {
    "aws_instance",
    "aws_eks_cluster",
    "aws_eks_node_group",
    "aws_db_instance",
    "aws_rds_cluster",
    "aws_elasticsearch_domain",
    "aws_opensearch_domain",
    "aws_nat_gateway",
    "aws_lb",
}


def load_plan(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("plan JSON must be an object")
    return data


def summarize(plan: dict[str, Any]) -> dict[str, Any]:
    changes = plan.get("resource_changes") or []
    counts = {"create": 0, "update": 0, "delete": 0, "replace": 0, "unknown": 0}
    hot = []
    for change in changes:
        actions = (change.get("change") or {}).get("actions") or []
        rtype = change.get("type") or "unknown"
        addr = change.get("address") or rtype
        after_unknown = (change.get("change") or {}).get("after_unknown") or {}
        if "delete" in actions and "create" in actions:
            counts["replace"] += 1
        elif "create" in actions:
            counts["create"] += 1
        elif "update" in actions:
            counts["update"] += 1
        elif "delete" in actions:
            counts["delete"] += 1
        if after_unknown:
            counts["unknown"] += 1
        if rtype in COST_TOUCH_RESOURCES and any(a in actions for a in ("create", "delete", "update")):
            hot.append({"address": addr, "type": rtype, "actions": actions})
    return {"counts": counts, "hot": hot, "total": len(changes)}


def violations(summary: dict[str, Any]) -> list[str]:
    c = summary["counts"]
    out = []
    if c["delete"] > DESTROY_MAX:
        out.append(f"destroy count {c['delete']} exceeds {DESTROY_MAX}")
    if c["create"] > CREATE_MAX:
        out.append(f"create count {c['create']} exceeds {CREATE_MAX}")
    if c["unknown"] > UNKNOWN_MAX:
        out.append(f"unknown-after values {c['unknown']} exceeds {UNKNOWN_MAX}")
    if c["replace"] and any(h["type"] in COST_TOUCH_RESOURCES for h in summary["hot"]):
        out.append("replace on cost-sensitive resource (EKS/RDS/LB/NAT/OpenSearch)")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Terraform plan blast-radius guard")
    parser.add_argument("--plan", required=True, help="Path to terraform show -json file")
    parser.add_argument("--json", action="store_true", help="Machine output")
    args = parser.parse_args()
    plan_path = Path(args.plan)
    if not plan_path.exists():
        print(f"missing plan file: {plan_path}", file=sys.stderr)
        return 2
    summary = summarize(load_plan(plan_path))
    bad = violations(summary)
    payload = {"ok": not bad, "violations": bad, **summary}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("terraform_plan_guard")
        print(json.dumps(summary["counts"]))
        print(f"hot_resources={len(summary['hot'])} total_changes={summary['total']}")
        for item in bad:
            print(f"BLOCK {item}")
        if not bad:
            print("PASS plan inside policy")
    return 2 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
