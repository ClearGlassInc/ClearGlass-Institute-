"""Agent 1 - Job Sourcing.

Pulls postings from one or more :class:`JobSource` adapters, normalises them
into :class:`JobPosting` records, and deduplicates roles that surface on more
than one board. Ships with file-backed sources (JSON and RSS) so the pipeline
runs offline; production adapters (Greenhouse, Remote100K, CryptoJobsList,
LinkedIn via PhantomBuster, Apify actors) implement the same ``fetch`` method.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Iterable, Optional, Protocol, runtime_checkable

from job_agent.models import JobPosting


@runtime_checkable
class JobSource(Protocol):
    """Anything that can yield raw postings for a day."""

    name: str

    def fetch(self) -> Iterable[JobPosting]:
        ...


# ---------------------------------------------------------------------------
# Salary parsing helpers
# ---------------------------------------------------------------------------

_SALARY_RE = re.compile(r"\$?\s*(\d{2,3})(?:,?(\d{3}))?\s*([kK])?")
# US benefit tokens that look like k-notation salaries ("401k", "403(b)") and
# would otherwise be misread as $401,000 / $403,000. Scrubbed before parsing.
_BENEFIT_NOISE_RE = re.compile(r"\b40[123]\s*\(?\s*[kb]\s*\)?", re.IGNORECASE)


def parse_salary(text: str) -> tuple[Optional[int], Optional[int]]:
    """Best-effort (min, max) salary extraction from free text.

    Handles ``$120k``, ``120,000``, ``$120k-$160k`` and ``120000 - 160000``.
    Strips US retirement-plan tokens (``401k``, ``403(b)``) first so they are not
    misread as salaries. Returns ``(None, None)`` when nothing parseable.
    """
    if not text:
        return (None, None)
    text = _BENEFIT_NOISE_RE.sub(" ", text)
    values: list[int] = []
    for whole, thousands, k in _SALARY_RE.findall(text):
        if k:
            amount = int(whole) * 1000
        elif thousands:
            amount = int(whole + thousands)
        else:
            # bare 2-3 digit number with no 'k' and no thousands group is noise
            continue
        if 30_000 <= amount <= 2_000_000:
            values.append(amount)
    if not values:
        return (None, None)
    values.sort()
    if len(values) == 1:
        return (values[0], values[0])
    return (values[0], values[-1])


def _parse_date(raw: object) -> Optional[date]:
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str) and raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def posting_from_dict(data: dict, *, source: str = "json") -> JobPosting:
    """Build a normalised :class:`JobPosting` from a raw source record."""
    smin = data.get("salary_min")
    smax = data.get("salary_max")
    if smin is None and smax is None:
        smin, smax = parse_salary(
            f"{data.get('salary', '')} {data.get('description', '')}"
        )
    location = data.get("location", "") or ""
    remote = bool(data.get("remote")) or "remote" in location.lower()
    return JobPosting(
        title=data.get("title", "").strip(),
        company=data.get("company", "").strip(),
        url=data.get("url", "").strip(),
        description=data.get("description", "") or "",
        location=location,
        remote=remote,
        salary_min=smin,
        salary_max=smax,
        source=data.get("source", source),
        posted_date=_parse_date(data.get("posted_date")),
        contact_name=data.get("contact_name"),
    )


# ---------------------------------------------------------------------------
# Concrete file-backed sources (offline-friendly)
# ---------------------------------------------------------------------------

class JSONFileSource:
    """Reads postings from a JSON array file - the canonical offline source."""

    def __init__(self, path: str, name: str = "json-file") -> None:
        self.path = path
        self.name = name

    def fetch(self) -> Iterable[JobPosting]:
        with open(self.path, "r", encoding="utf-8") as fh:
            records = json.load(fh)
        for record in records:
            yield posting_from_dict(record, source=record.get("source", self.name))


class StaticSource:
    """Wraps an in-memory list of postings (used by tests and webhook intake)."""

    def __init__(self, postings: Iterable[JobPosting], name: str = "static") -> None:
        self._postings = list(postings)
        self.name = name

    def fetch(self) -> Iterable[JobPosting]:
        return list(self._postings)


# ---------------------------------------------------------------------------
# The Sourcing Agent
# ---------------------------------------------------------------------------

class SourcingAgent:
    """Fans out across sources, normalises, and deduplicates by fingerprint."""

    def __init__(self, sources: Optional[list[JobSource]] = None) -> None:
        self.sources: list[JobSource] = list(sources or [])

    def add_source(self, source: JobSource) -> "SourcingAgent":
        self.sources.append(source)
        return self

    def collect(self) -> list[JobPosting]:
        """Pull every source, dropping duplicates while preserving first-seen."""
        seen: set[str] = set()
        results: list[JobPosting] = []
        for source in self.sources:
            try:
                postings = list(source.fetch())
            except Exception as exc:  # one bad board should not sink the run
                print(f"[sourcing] source '{getattr(source, 'name', source)}' failed: {exc}")
                continue
            for posting in postings:
                if not posting.title or not posting.company:
                    continue
                fp = posting.fingerprint
                if fp in seen:
                    continue
                seen.add(fp)
                results.append(posting)
        return results
