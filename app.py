#!/usr/bin/env python3
"""ClearGlassInc Artemis API bridge.

Exposes intelligence outputs to frontend clients and orchestrators.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify

CONFIG_PATH = Path("clearglassinc.json")


def load_config() -> Dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


CONFIG = load_config()
DB_PATH = Path(CONFIG["data_sources"]["databases"]["sqlite"]["path"])

app = Flask("clearglassinc_artemis_api")


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/api/health")
def health() -> Any:
    return jsonify(
        {
            "status": "ok",
            "system": "ClearGlassInc Artemis",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )


@app.route("/api/status")
def status() -> Any:
    """Return latest predictions for frontend dashboards."""
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT prediction_date, target_date, sector, predicted_index,
                   confidence_score, scenario
            FROM predictions
            ORDER BY prediction_date DESC
            LIMIT 25
            """
        ).fetchall()

    payload: List[Dict[str, Any]] = [dict(r) for r in rows]
    return jsonify({"count": len(payload), "predictions": payload})


@app.route("/api/market")
def market() -> Any:
    """Return recent market analysis output."""
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT analysis_date, sector, market_sentiment,
                   growth_score, risk_level, analysis_json
            FROM analysis_results
            ORDER BY analysis_date DESC
            LIMIT 25
            """
        ).fetchall()

    payload: List[Dict[str, Any]] = []
    for row in rows:
        record = dict(row)
        if record.get("analysis_json"):
            try:
                record["analysis_json"] = json.loads(record["analysis_json"])
            except json.JSONDecodeError:
                pass
        payload.append(record)

    return jsonify({"count": len(payload), "market": payload})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
