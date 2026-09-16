"""Job Automation Agent stack.

A four-agent pipeline that sources, scores, personalises, and tracks
applications to high-paying roles:

* Agent 1 - :mod:`job_agent.sourcing`        (find jobs daily)
* Agent 2 - :mod:`job_agent.scoring`         (filter + score 1-10)
* Agent 3 - :mod:`job_agent.personalization` (tailor resume + outreach)
* Agent 4 - :mod:`job_agent.tracking`        (apply + log + follow up)

plus an :mod:`job_agent.intelligence` Opportunity Intelligence Layer, wired
together by :class:`job_agent.pipeline.JobAutomationPipeline`.
"""

from job_agent.config import SearchProfile, ScoringWeights
from job_agent.models import (
    Application, ApplicationKit, ApplicationStatus, JobPosting, ScoredJob,
)
from job_agent.pipeline import JobAutomationPipeline

__version__ = "0.1.0"

__all__ = [
    "SearchProfile",
    "ScoringWeights",
    "JobPosting",
    "ScoredJob",
    "ApplicationKit",
    "Application",
    "ApplicationStatus",
    "JobAutomationPipeline",
]
