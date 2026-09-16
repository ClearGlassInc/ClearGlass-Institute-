"""Self-contained ClearPulse demo - the design doc's end-to-end trace walk.

Run with::

    python3 -m clearpulse.demo

Requires no external services; it drives the in-process pipeline and prints the
scored envelopes, raised alerts, and any compromised-account correlations.
"""

from __future__ import annotations

import json
import os
import tempfile

from clearpulse.pipeline import ClearPulsePipeline


def main() -> None:
    pipeline = ClearPulsePipeline()

    print("== 09:00 MRI procedure claim for P-9912 ==")
    mri = {
        "patient_id": "P-9912", "provider_id": "DR-442", "dept": "RADIOLOGY",
        "procedures": [{"cpt_code": "73721",
                        "service_start": "2026-06-01T09:00:00Z",
                        "service_end": "2026-06-01T09:45:00Z"}],
    }
    for env in pipeline.process_encounter(mri):
        print(f"   score={env.score} level={env.level}")

    print("== 09:10 office consultation for P-9912 (different provider) ==")
    consult = {
        "patient_id": "P-9912", "provider_id": "DR-999", "dept": "CARDIOLOGY",
        "procedures": [{"cpt_code": "99213",
                        "service_start": "2026-06-01T09:10:00Z",
                        "service_end": "2026-06-01T09:25:00Z"}],
    }
    for env in pipeline.process_encounter(consult):
        print(f"   score={env.score} level={env.level} "
              f"reasons={env.triggering_facts}")

    print("== access spike: dermatology nurse opens 50 charts in an hour ==")
    for i in range(50):
        pipeline.process_access(
            {"user_id": "NURSE-7", "patient_id": f"P-{i}", "dept": "DERMATOLOGY",
             "timestamp": "2026-06-01T09:20:00Z"},
            baseline_median=8, baseline_std=4,
        )

    print("== 09:30 compliance auto-scan finds an unencrypted export ==")
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "discharge_report.csv")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("name,mrn,ssn\nJane Doe,MRN 1234567,123-45-6789\n")
        pipeline.scan_paths([tmp])

    print("\n== unified alert feed ==")
    for alert in pipeline.router.accepted:
        print(f"   [{alert.severity}] {alert.alert_type}: {alert.summary}")

    if pipeline.router.correlations:
        print("\n== correlations ==")
        print(json.dumps(pipeline.router.correlations, indent=2))


if __name__ == "__main__":
    main()
