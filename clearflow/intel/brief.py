"""Critical Intelligence Brief ingestion and domain routing.

The morning brief is a handful of free-text headlines. This module turns each
into an :class:`~clearflow.models.IntelSignal` and routes it to the domain it
informs, using a small keyword map. Routing is deliberately simple and plainly
inspectable - the goal is to attach the right signal to the right work item, not
to do NLP.
"""

from __future__ import annotations

from clearflow.models import IntelSignal

# Domain -> keywords that route a headline to it. First domain with the most
# keyword hits wins; ties fall back to declaration order.
DEFAULT_ROUTES: dict[str, list[str]] = {
    "AI Automation": ["ai", "agent", "automation", "workflow", "llm", "model"],
    "Cybersecurity": ["cyber", "vulnerab", "supply chain", "exploit", "breach",
                       "threat", "risk", "ransomware"],
    "Personal Brand": ["linkedin", "brand", "audience", "engagement", "post",
                        "trend", "content"],
    "Research": ["quantum", "error correction", "milestone", "research",
                 "breakthrough"],
}


class IntelRouter:
    """Routes free-text brief headlines to the domain they inform."""

    def __init__(self, routes: dict[str, list[str]] | None = None) -> None:
        self.routes = routes or DEFAULT_ROUTES

    def _score(self, headline: str) -> tuple[str | None, list[str]]:
        lowered = headline.lower()
        best_domain: str | None = None
        best_hits: list[str] = []
        for domain, keywords in self.routes.items():
            hits = [kw for kw in keywords if kw in lowered]
            if len(hits) > len(best_hits):
                best_domain, best_hits = domain, hits
        return best_domain, best_hits

    def route(self, headlines: list[str]) -> list[IntelSignal]:
        """Convert headlines into routed :class:`IntelSignal` objects."""
        signals: list[IntelSignal] = []
        for headline in headlines:
            domain, hits = self._score(headline)
            signals.append(IntelSignal(
                headline=headline.strip(),
                routed_to=domain,
                keywords=hits,
            ))
        return signals

    @staticmethod
    def for_domain(signals: list[IntelSignal], domain: str) -> list[IntelSignal]:
        """Filter already-routed signals down to a single domain."""
        return [s for s in signals if s.routed_to == domain]
