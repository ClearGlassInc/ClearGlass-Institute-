from artemis.agents.tools import tool_query_ontology, tool_create_case


async def run_mission_workflow(event: dict) -> dict:
    triage = {
        "event_id": event["event_id"],
        "risk_score": 0.86,
        "priority": "high",
    }

    enrichment = await tool_query_ontology(
        mission_id=event["mission_id"],
        query=f"match entities near event {event['event_id']}"
    )

    case = await tool_create_case(
        mission_id=event["mission_id"],
        title=f"Provisional case for {event['event_id']}",
        evidence=enrichment,
    )

    recommendation = {
        "recommended_action": "escalate_case",
        "case_id": case["case_id"],
        "confidence": 0.79,
        "rationale": "Pattern overlap and known entity adjacency"
    }
    return {"triage": triage, "enrichment": enrichment, "recommendation": recommendation}
