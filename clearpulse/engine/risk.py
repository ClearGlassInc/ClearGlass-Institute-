"""Dynamic Risk Scoring - the part of the pipeline where the pulse races.

Weights live in ``clearpulse/config/risk_rules.yaml`` so the compliance team can
tune the model without redeploying code. If PyYAML or the file is unavailable,
:data:`DEFAULT_RULES` (an identical baseline) is used, keeping the engine
importable in minimal environments.

The scorer is a pure function of explicit signals - it does no I/O - so it is
fully unit-testable and every component point is traceable back to a fact.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional

from clearpulse.models import ObservableFact, RiskEnvelope

# Baseline rules - mirrors the shipped YAML so imports never hard-fail.
DEFAULT_RULES: dict[str, Any] = {
    "version": 1,
    "thresholds": {"low_max": 25, "medium_max": 69, "high_min": 70},
    "factors": {
        "temporal_billing_overlap": {"max_points": 40, "overlap_ratio_trigger": 0.6},
        "unusual_procedure_mix": {"max_points": 20},
        "access_volume_spike": {"max_points": 50, "zscore_full_points": 6.0},
        "high_risk_patient": {"max_points": 10},
        "off_hours_activity": {"max_points": 10, "business_start_hour": 7,
                               "business_end_hour": 19},
    },
    "total_cap": 100,
}

_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "risk_rules.yaml")


def load_rules(path: Optional[str] = None) -> dict[str, Any]:
    """Load scoring rules from YAML, falling back to :data:`DEFAULT_RULES`."""
    target = path or _RULES_PATH
    try:
        import yaml  # optional dependency
    except ImportError:
        return DEFAULT_RULES
    try:
        with open(target, "r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
    except (OSError, ValueError):
        return DEFAULT_RULES
    return loaded if isinstance(loaded, dict) else DEFAULT_RULES


def overlap_ratio(a: ObservableFact, b: ObservableFact) -> float:
    """Jaccard-style time fraction: intersection / min(duration_a, duration_b).

    Returns 0.0 when the claims do not overlap or either has zero duration.
    """
    latest_start = max(a.service_start, b.service_start)
    earliest_end = min(a.service_end, b.service_end)
    intersection = (earliest_end - latest_start).total_seconds()
    if intersection <= 0:
        return 0.0
    shortest = min(a.duration_seconds, b.duration_seconds)
    if shortest <= 0:
        return 0.0
    return intersection / shortest


class RiskScorer:
    """Computes an explainable :class:`RiskEnvelope` for a transaction."""

    def __init__(self, rules: Optional[dict[str, Any]] = None) -> None:
        self.rules = rules or load_rules()

    def _level(self, score: int) -> str:
        thresholds = self.rules["thresholds"]
        if score >= thresholds["high_min"]:
            return "high"
        if score <= thresholds["low_max"]:
            return "low"
        return "medium"

    def score(
        self,
        fact: ObservableFact,
        overlaps: Optional[list[ObservableFact]] = None,
        *,
        access_zscore: float = 0.0,
        unusual_procedure_mix: bool = False,
    ) -> RiskEnvelope:
        """Score one transaction from its correlated signals.

        ``overlaps`` are the concurrent claims for the same patient (from the
        sliding window); ``access_zscore`` comes from the access sub-engine.
        """
        factors = self.rules["factors"]
        components: dict[str, int] = {}
        reasons: list[str] = []

        # --- Temporal billing overlap ---
        cfg = factors["temporal_billing_overlap"]
        best_ratio = 0.0
        best_other: Optional[ObservableFact] = None
        for other in overlaps or []:
            ratio = overlap_ratio(fact, other)
            if ratio > best_ratio:
                best_ratio, best_other = ratio, other
        if best_ratio > cfg["overlap_ratio_trigger"]:
            components["temporal_billing_overlap"] = int(cfg["max_points"])
            reasons.append(
                f"Temporal billing overlap {best_ratio:.0%} with "
                f"{best_other.cpt_code if best_other else '?'} "
                f"(provider {best_other.provider_id if best_other else '?'})"
            )

        # --- Unusual procedure mix ---
        if unusual_procedure_mix:
            pts = int(factors["unusual_procedure_mix"]["max_points"])
            components["unusual_procedure_mix"] = pts
            reasons.append("Unusual procedure mix for encounter")

        # --- Access volume spike (scaled by z-score, capped) ---
        cfg = factors["access_volume_spike"]
        if access_zscore > 0:
            full = float(cfg.get("zscore_full_points", 6.0)) or 6.0
            fraction = min(1.0, access_zscore / full)
            pts = int(round(cfg["max_points"] * fraction))
            if pts > 0:
                components["access_volume_spike"] = pts
                reasons.append(f"Access volume spike (z={access_zscore:.1f})")

        # --- High-risk (VIP) patient ---
        if fact.vip:
            pts = int(factors["high_risk_patient"]["max_points"])
            components["high_risk_patient"] = pts
            reasons.append("High-risk/VIP patient record")

        # --- Off-hours activity ---
        cfg = factors["off_hours_activity"]
        hour = fact.service_start.hour
        if hour < cfg["business_start_hour"] or hour >= cfg["business_end_hour"]:
            components["off_hours_activity"] = int(cfg["max_points"])
            reasons.append(f"Off-hours activity at {hour:02d}:00")

        raw = sum(components.values())
        score = min(raw, int(self.rules["total_cap"]))
        return RiskEnvelope(
            trace_id=fact.trace_id,
            score=score,
            level=self._level(score),
            components=components,
            triggering_facts=reasons,
        )
