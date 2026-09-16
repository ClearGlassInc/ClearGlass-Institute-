#!/usr/bin/env python3
"""Multi-window SLO burn-rate gate.

Use with Azure Monitor / App Insights export or any request+error counters.
Blocks a release when short-window burn exceeds budget.
"""
from __future__ import annotations

import argparse
import json
import sys


HOURS = {"5m": 5 / 60, "1h": 1.0, "6h": 6.0, "24h": 24.0, "3d": 72.0}


def burn_rate(errors: float, requests: float, slo: float, window_h: float, period_h: float = 30 * 24) -> float:
    if requests <= 0:
        return 0.0
    error_ratio = errors / requests
    allowed = max(1e-12, (100.0 - slo) / 100.0)
    return (error_ratio / allowed) * (period_h / window_h)


def main() -> int:
    parser = argparse.ArgumentParser(description="Azure-oriented SLO burn gate")
    parser.add_argument("--slo", type=float, default=99.9)
    parser.add_argument("--window", default="1h", choices=sorted(HOURS))
    parser.add_argument("--errors", type=float, required=True)
    parser.add_argument("--requests", type=float, required=True)
    parser.add_argument("--burn", type=float, default=14.4, help="page threshold (1h/14.4 is classic 2%% budget in 1h)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    window_h = HOURS[args.window]
    rate = burn_rate(args.errors, args.requests, args.slo, window_h)
    error_ratio = args.errors / args.requests if args.requests else 0.0
    payload = {
        "slo": args.slo,
        "window": args.window,
        "error_ratio": round(error_ratio, 6),
        "burn_rate": round(rate, 3),
        "threshold": args.burn,
        "page": rate >= args.burn,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        state = "PAGE" if payload["page"] else "OK"
        print(
            f"{state} slo={args.slo} window={args.window} "
            f"error_ratio={error_ratio:.6f} burn={rate:.3f} threshold={args.burn}"
        )
    return 2 if payload["page"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
