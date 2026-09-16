def enforce_action_policy(req: dict) -> dict:
    must_approve = (
        req["risk_score"] >= 0.8
        or req["uncertainty"] >= 0.35
        or req["cross_compartment"]
    )
    return {
        "allow_automatic": not must_approve,
        "requires_human_approval": must_approve,
        "reason": "risk/uncertainty/compartment gate triggered" if must_approve else "auto-allowed",
    }
