"""Agent 4 - Apply + Track + Follow-up.

Holds the application tracker (the Airtable/Sheets "base" in the design brief)
and the follow-up clock. The tracker is an in-memory store with JSON
persistence and a pluggable :class:`TrackerSink` so the same rows can be mirrored
to Airtable, Google Sheets, or a webhook in production. Application submission is
intentionally assisted, not silent-auto: it stages a kit and records the row,
then exposes the apply URL for the human-in-the-loop click described in the
daily flow.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Iterable, Optional, Protocol

from job_agent.config import SearchProfile
from job_agent.models import (
    Application, ApplicationKit, ApplicationStatus, ScoredJob,
)


class TrackerSink(Protocol):
    """External mirror for tracker rows (Airtable, Sheets, webhook, ...)."""

    def upsert(self, application: Application) -> None:
        ...


class TrackingAgent:
    """Manages applications, follow-up scheduling, and follow-up copy."""

    def __init__(
        self,
        profile: Optional[SearchProfile] = None,
        sink: Optional[TrackerSink] = None,
    ) -> None:
        self.profile = profile or SearchProfile()
        self.sink = sink
        self._apps: dict[str, Application] = {}

    # --------------------------------------------------------------- intake
    def stage(self, scored: ScoredJob, kit: Optional[ApplicationKit] = None) -> Application:
        """Create a QUEUED tracker row for a scored job (ready for review)."""
        app = Application(
            job=scored.job,
            score=scored.score,
            reasons=list(scored.reasons),
            kit=kit,
            status=ApplicationStatus.QUEUED,
            contact_name=scored.job.contact_name,
        )
        self._apps[app.id] = app
        self._mirror(app)
        return app

    def mark_applied(self, app_id: str, *, on: Optional[date] = None) -> Application:
        """Record a submission and arm the follow-up clock."""
        app = self._apps[app_id]
        applied = on or date.today()
        app.status = ApplicationStatus.APPLIED
        app.applied_date = applied
        app.follow_up_date = applied + timedelta(days=self.profile.follow_up_days)
        self._mirror(app)
        return app

    def set_status(self, app_id: str, status: ApplicationStatus) -> Application:
        app = self._apps[app_id]
        app.status = status
        self._mirror(app)
        return app

    # ----------------------------------------------------------- follow-ups
    def due_for_follow_up(self, *, today: Optional[date] = None) -> list[Application]:
        """Applications whose follow-up date has arrived and that are still open."""
        ref = today or date.today()
        open_states = {ApplicationStatus.APPLIED}
        return [
            app for app in self._apps.values()
            if app.status in open_states
            and app.follow_up_date is not None
            and app.follow_up_date <= ref
        ]

    def follow_up_message(self, app: Application) -> str:
        """Generate the 3-5 day nudge from the design brief."""
        name = app.contact_name or app.job.contact_name or "there"
        greeting = f"Hi {name}," if (app.contact_name or app.job.contact_name) else "Hi there,"
        anchor = app.reasons[0].lower() if app.reasons else "my background in BD and operations"
        return (
            f"{greeting} wanted to follow up - I'm genuinely excited about the "
            f"{app.job.title} role at {app.job.company} given {anchor}. "
            "Happy to share more or connect whenever it's useful."
        )

    def record_follow_up(self, app_id: str, *, on: Optional[date] = None) -> Application:
        """Mark that a follow-up was sent and re-arm the next nudge."""
        app = self._apps[app_id]
        sent = on or date.today()
        app.status = ApplicationStatus.FOLLOWED_UP
        app.follow_up_date = sent + timedelta(days=self.profile.follow_up_days)
        self._mirror(app)
        return app

    # ----------------------------------------------------------------- views
    @property
    def applications(self) -> list[Application]:
        return list(self._apps.values())

    def get(self, app_id: str) -> Application:
        return self._apps[app_id]

    def _mirror(self, app: Application) -> None:
        if self.sink is not None:
            try:
                self.sink.upsert(app)
            except Exception as exc:  # mirroring must never break the pipeline
                print(f"[tracking] sink upsert failed for {app.id}: {exc}")

    # ----------------------------------------------------------- persistence
    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([a.to_dict() for a in self.applications], fh, indent=2)


class JSONTrackerSink:
    """Append-only JSON-lines mirror - the simplest durable tracker backend."""

    def __init__(self, path: str) -> None:
        self.path = path

    def upsert(self, application: Application) -> None:
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(application.to_dict()) + "\n")
