"""End-to-end Job Automation Agent pipeline (single-process reference path).

Wires the four agents - sourcing -> scoring -> personalization -> tracking -
into one object so the CLI, the demo, and any scheduled trigger share identical
behaviour. In a deployed setup each agent can run as its own scheduled job
(7 AM scrape, 7:10 score, ...); the seams here (``sourcing``, ``scoring``,
``personalization``, ``tracking``, ``intelligence``) are the swap points.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from job_agent.config import SearchProfile
from job_agent.intelligence import IntelligenceLayer
from job_agent.llm import LLMEngine, HeuristicEngine, default_engine
from job_agent.models import Application, ScoredJob
from job_agent.personalization import PersonalizationAgent
from job_agent.scoring import ScoringAgent
from job_agent.sourcing import JobSource, SourcingAgent
from job_agent.tracking import TrackerSink, TrackingAgent


class JobAutomationPipeline:
    """Reference orchestration of the full daily flow."""

    def __init__(
        self,
        profile: Optional[SearchProfile] = None,
        master_resume: str = "",
        sources: Optional[list[JobSource]] = None,
        engine: Optional[LLMEngine] = None,
        sink: Optional[TrackerSink] = None,
    ) -> None:
        self.profile = profile or SearchProfile()
        self.engine = engine or default_engine()
        self.sourcing = SourcingAgent(sources)
        self.scoring = ScoringAgent(self.profile, engine=self.engine)
        self.personalization = PersonalizationAgent(
            master_resume, self.profile, engine=self.engine,
        )
        self.tracking = TrackingAgent(self.profile, sink=sink)
        self.intelligence = IntelligenceLayer()

    def run_daily(self, *, today: Optional[date] = None) -> list[Application]:
        """The 7 AM job: source -> score/filter -> personalise -> stage rows.

        Returns the staged applications (the day's reviewed shortlist), each
        carrying its tailored :class:`~job_agent.models.ApplicationKit`.
        """
        postings = self.sourcing.collect()
        shortlist: list[ScoredJob] = self.scoring.rank(postings, today=today)
        staged: list[Application] = []
        for scored in shortlist:
            kit = self.personalization.build(scored)
            staged.append(self.tracking.stage(scored, kit))
        return staged

    def follow_ups_due(self, *, today: Optional[date] = None) -> list[dict[str, Any]]:
        """Generate ready-to-send follow-up messages for applications due."""
        out: list[dict[str, Any]] = []
        for app in self.tracking.due_for_follow_up(today=today):
            out.append({
                "application_id": app.id,
                "company": app.job.company,
                "title": app.job.title,
                "message": self.tracking.follow_up_message(app),
            })
        return out

    def intelligence_report(self) -> dict[str, Any]:
        """Run the Opportunity Intelligence Layer over the tracker."""
        return self.intelligence.analyze(self.tracking.applications)
