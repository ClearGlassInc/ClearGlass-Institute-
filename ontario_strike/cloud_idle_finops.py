#!/usr/bin/env python3
"""Flag idle or oversized cloud inventory from a local JSON export.

Expected records:
  {"id": "...", "type": "ec2|rds|aks|aks_node|disk|nat|lb",
   "region": "...", "state": "running|stopped|available",
   "cpu_p95": 0-100, "age_days": int, "monthly_usd": float,
   "unattached": bool, "name": "..."}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def score(item: dict[str, Any]) -> dict[str, Any] | None:
    reasons = []
    monthly = float(item.get("monthly_usd") or 0)
    cpu = item.get("cpu_p95")
    state = (item.get("state") or "").lower()
    rtype = (item.get("type") or "").lower()
    if item.get("unattached") and rtype in {"disk", "ebs", "managed_disk"}:
        reasons.append("unattached disk")
    if state in {"stopped", "available"} and monthly >= 5:
        reasons.append(f"stopped/available still billed ({state})")
    if cpu is not None and float(cpu) < 8 and state == "running" and monthly >= 20:
        reasons.append(f"running hot-cost idle cpu_p95={cpu}")
    if rtype in {"nat", "nat_gateway"} and monthly >= 30:
        reasons.append("NAT gateway is a standing tax — check egress pattern")
    if not reasons:
        return None
    return {
        "id": item.get("id") or item.get("name"),
        "type": rtype,
        "region": item.get("region"),
        "monthly_usd": monthly,
        "reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Idle cloud spend finder")
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--min-usd", type=float, default=0)
    args = parser.parse_args()
    path = Path(args.inventory)
    if not path.exists():
        print(f"missing inventory: {path}", file=sys.stderr)
        return 2
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw if isinstance(raw, list) else raw.get("resources") or raw.get("items") or []
    findings = []
    total = 0.0
    for item in rows:
        hit = score(item)
        if hit and hit["monthly_usd"] >= args.min_usd:
            findings.append(hit)
            total += hit["monthly_usd"]
    findings.sort(key=lambda x: x["monthly_usd"], reverse=True)
    print(json.dumps({"findings": findings, "monthly_usd_at_risk": round(total, 2), "n": len(findings)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
