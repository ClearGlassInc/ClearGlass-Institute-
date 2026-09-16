"""Ingestion Parser - validate, enrich, and flatten raw feeds into facts.

The parser is deliberately tolerant of two input shapes for an encounter:

1. A simplified ClearPulse bundle (one patient/provider, many procedures)::

       {
         "patient_id": "P-9912",
         "provider_id": "DR-442",
         "dept": "RADIOLOGY",
         "vip": false,
         "procedures": [
           {"cpt_code": "73721",
            "service_start": "2026-06-01T09:00:00Z",
            "service_end":   "2026-06-01T09:45:00Z",
            "diagnosis_codes": ["M25.561"]}
         ]
       }

2. A subset of a raw FHIR ``Bundle`` whose ``entry[].resource`` items are
   ``Procedure``/``Claim`` resources. Only the fields ClearPulse needs are read.

Every emitted :class:`~clearpulse.models.ObservableFact` is decorated with a
fresh ClearPulse Trace ID unless the caller supplies one (so a re-score can
reuse the original thread).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from clearpulse.models import AccessEvent, ObservableFact, new_trace_id


def _parse_ts(value: Any) -> datetime:
    """Parse an ISO-8601 timestamp, accepting a trailing ``Z`` for UTC."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        raise ValueError(f"timestamp must be str or datetime, got {type(value)!r}")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _normalise_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """Coerce a raw FHIR-ish ``Bundle`` into the simplified ClearPulse shape."""
    if "procedures" in bundle:
        return bundle
    if bundle.get("resourceType") != "Bundle":
        raise ValueError("unrecognised encounter payload: expected 'procedures' "
                         "or a FHIR Bundle")
    procedures: list[dict[str, Any]] = []
    patient_id = provider_id = dept = None
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        rtype = resource.get("resourceType")
        if rtype not in {"Procedure", "Claim"}:
            continue
        patient_id = patient_id or _ref_id(resource.get("subject") or resource.get("patient"))
        provider_id = provider_id or _ref_id(resource.get("performer") or resource.get("provider"))
        period = resource.get("performedPeriod") or resource.get("billablePeriod") or {}
        procedures.append({
            "cpt_code": _coding_code(resource.get("code") or resource.get("type")),
            "service_start": period.get("start"),
            "service_end": period.get("end"),
            "diagnosis_codes": [_coding_code(d) for d in resource.get("diagnosis", [])],
        })
    return {
        "patient_id": patient_id,
        "provider_id": provider_id,
        "dept": dept,
        "procedures": procedures,
    }


def _ref_id(ref: Any) -> Optional[str]:
    """Resolve a logical id from a FHIR reference, performer list, or actor wrap.

    Handles the common shapes: a plain ``Reference`` dict, a ``Procedure``
    ``performer`` list whose entries wrap the reference under ``actor``, and a
    ``Claim`` single-provider ``Reference``.
    """
    if isinstance(ref, list):
        for item in ref:
            resolved = _ref_id(item)
            if resolved:
                return resolved
        return None
    if isinstance(ref, dict):
        if "actor" in ref:
            return _ref_id(ref["actor"])
        reference = ref.get("reference", "")
        if reference:
            return reference.split("/")[-1]
        return ref.get("id")
    return None


def _coding_code(code: Any) -> str:
    if isinstance(code, dict):
        codings = code.get("coding") or []
        if codings:
            return codings[0].get("code", "")
        return code.get("code", "")
    return str(code) if code is not None else ""


def parse_encounter_bundle(
    bundle: dict[str, Any],
    *,
    trace_id: Optional[str] = None,
    event_type: str = "procedure_claim",
) -> list[ObservableFact]:
    """Extract one :class:`ObservableFact` per encounter-procedure pair.

    All procedures in a single bundle share one trace id (the encounter thread).
    """
    normalised = _normalise_bundle(bundle)
    patient_id = normalised.get("patient_id")
    provider_id = normalised.get("provider_id")
    if not patient_id or not provider_id:
        raise ValueError("encounter bundle missing patient_id/provider_id")

    tid = trace_id or new_trace_id()
    dept = normalised.get("dept") or "UNKNOWN"
    vip = bool(normalised.get("vip", False))

    facts: list[ObservableFact] = []
    for proc in normalised.get("procedures", []):
        facts.append(ObservableFact(
            trace_id=tid,
            event_type=event_type,
            patient_id=str(patient_id),
            provider_id=str(provider_id),
            cpt_code=str(proc.get("cpt_code", "")),
            service_start=_parse_ts(proc["service_start"]),
            service_end=_parse_ts(proc["service_end"]),
            dept=str(proc.get("dept") or dept),
            diagnosis_codes=list(proc.get("diagnosis_codes", [])),
            vip=vip,
        ))
    if not facts:
        raise ValueError("encounter bundle contained no procedures")
    return facts


def parse_access_log_entry(
    entry: dict[str, Any],
    *,
    trace_id: Optional[str] = None,
) -> AccessEvent:
    """Normalise one ADT/staff access-log record into an :class:`AccessEvent`."""
    return AccessEvent(
        trace_id=trace_id or new_trace_id(),
        user_id=str(entry["user_id"]),
        patient_id=str(entry["patient_id"]),
        dept=str(entry.get("dept", "UNKNOWN")),
        timestamp=_parse_ts(entry["timestamp"]),
        action=str(entry.get("action", "record_open")),
    )
