from datetime import datetime, timezone


async def tool_query_ontology(mission_id: str, query: str) -> dict:
    return {
        "mission_id": mission_id,
        "query": query,
        "results": [{"entity_id": "ORG-4421", "confidence": 0.78}],
        "ts": datetime.now(timezone.utc).isoformat(),
    }


async def tool_create_case(mission_id: str, title: str, evidence: dict) -> dict:
    return {
        "case_id": f"CASE-{mission_id[:4]}-001",
        "mission_id": mission_id,
        "title": title,
        "evidence_count": len(evidence.get("results", [])),
    }
