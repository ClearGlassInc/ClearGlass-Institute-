"""Core data structures shared across the Job Automation Agent stack.

These are plain :mod:`dataclasses` with no third-party dependency, so every
agent (sourcing -> scoring -> personalization -> tracking) can be unit-tested
without an LLM key, Airtable, or any network access. The optional adapters in
:mod:`job_agent.llm` and :mod:`job_agent.tracking` adapt these to external
services at their edges.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Optional


def utcnow() -> datetime:
    """Timezone-aware UTC now (the whole pipeline correlates dates in UTC)."""
    return datetime.now(timezone.utc)


def new_id() -> str:
    """Short, unique identifier for tracked entities."""
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Agent 1 - sourcing output
# ---------------------------------------------------------------------------

@dataclass
class JobPosting:
    """A single role discovered by the Sourcing Agent.

    ``fingerprint`` is a stable hash of (title, company, normalised url) used to
    deduplicate the same role surfacing across multiple boards on the same day.
    """

    title: str
    company: str
    url: str
    description: str = ""
    location: str = ""
    remote: bool = False
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    source: str = "unknown"
    posted_date: Optional[date] = None
    contact_name: Optional[str] = None
    id: str = field(default_factory=new_id)

    @property
    def fingerprint(self) -> str:
        url = self.url.split("?", 1)[0].rstrip("/").lower()
        key = f"{self.title.strip().lower()}|{self.company.strip().lower()}|{url}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    @property
    def salary_top(self) -> Optional[int]:
        """Highest advertised figure, used for the >=100k gate."""
        if self.salary_max is not None:
            return self.salary_max
        return self.salary_min

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "url": self.url,
            "location": self.location,
            "remote": self.remote,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "source": self.source,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
            "contact_name": self.contact_name,
            "fingerprint": self.fingerprint,
        }


# ---------------------------------------------------------------------------
# Agent 2 - scoring output
# ---------------------------------------------------------------------------

@dataclass
class ScoredJob:
    """A posting plus its 1-10 fit score and the reasons behind it.

    ``components`` is the per-factor point breakdown so any score is explainable,
    mirroring the "Score + 3 bullet reasons" contract from the design brief.
    """

    job: JobPosting
    score: float
    reasons: list[str] = field(default_factory=list)
    components: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.job.to_dict(),
            "score": round(self.score, 1),
            "reasons": list(self.reasons),
            "components": dict(self.components),
        }


# ---------------------------------------------------------------------------
# Agent 3 - personalization output
# ---------------------------------------------------------------------------

@dataclass
class ApplicationKit:
    """Tailored collateral the Personalization Agent generates per role."""

    job_id: str
    resume_bullets: list[str] = field(default_factory=list)
    cover_message: str = ""
    outreach_message: str = ""
    engine: str = "heuristic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "resume_bullets": list(self.resume_bullets),
            "cover_message": self.cover_message,
            "outreach_message": self.outreach_message,
            "engine": self.engine,
        }


# ---------------------------------------------------------------------------
# Agent 4 - application tracking
# ---------------------------------------------------------------------------

class ApplicationStatus(str, Enum):
    """Lifecycle of a tracked application (the Airtable ``Status`` field)."""

    SOURCED = "Sourced"
    QUEUED = "Queued"
    APPLIED = "Applied"
    FOLLOWED_UP = "Followed Up"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    REJECTED = "Rejected"
    SKIPPED = "Skipped"


@dataclass
class Application:
    """One row in the tracker: a job, its kit, status, and follow-up clock."""

    job: JobPosting
    score: float
    reasons: list[str] = field(default_factory=list)
    kit: Optional[ApplicationKit] = None
    status: ApplicationStatus = ApplicationStatus.SOURCED
    applied_date: Optional[date] = None
    follow_up_date: Optional[date] = None
    contact_name: Optional[str] = None
    notes: str = ""
    id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.job.title,
            "company": self.job.company,
            "url": self.job.url,
            "score": round(self.score, 1),
            "status": self.status.value,
            "applied_date": self.applied_date.isoformat() if self.applied_date else None,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "contact_name": self.contact_name or self.job.contact_name,
            "reasons": list(self.reasons),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }
