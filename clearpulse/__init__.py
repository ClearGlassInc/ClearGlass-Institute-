"""ClearPulse - healthcare encounter triage, risk scoring, and compliance pipeline.

Copyright (c) 2025-2030 Clearglassinc. All Rights Reserved.

ClearPulse traces a single patient encounter from raw signal (FHIR encounter
bundles, ADT/staff access logs, billing claims) to an actionable, fully
attributable alert. Every stage carries an immutable ClearPulse Trace ID so a
risk score can always be unpacked back to the facts that triggered it.

Layering mirrors the sibling ``artemis`` package:

* :mod:`clearpulse.ingestion` - the data layer (normalise, timestamp, decorate).
* :mod:`clearpulse.engine`     - the logic layer (windowed correlation + risk).
* :mod:`clearpulse.compliance` - the security layer (at-rest PHI scanning).
* :mod:`clearpulse.alerts`     - dedup + correlation into a single alert feed.
* :mod:`clearpulse.backend`    - the FastAPI orchestration gateway.

The core engine depends only on the standard library so it can be exercised
without optional services (Redis, RocksDB, PostgreSQL) being present.
"""

__version__ = "0.1.0"
__copyright__ = "(c) 2025-2030 Clearglassinc. All Rights Reserved."
__system_name__ = "ClearPulse Triage & Compliance Pipeline"

from clearpulse.models import (
    AccessEvent,
    Alert,
    ComplianceFinding,
    ObservableFact,
    RiskEnvelope,
    new_trace_id,
)

__all__ = [
    "AccessEvent",
    "Alert",
    "ComplianceFinding",
    "ObservableFact",
    "RiskEnvelope",
    "new_trace_id",
    "__version__",
]
