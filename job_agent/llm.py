"""Pluggable language-model layer for the personalization and scoring agents.

The stack ships with two engines:

* :class:`HeuristicEngine` - deterministic, dependency-free, zero-key. It powers
  the demo and the test-suite and produces solid keyword-driven collateral.
* :class:`ClaudeEngine` - an optional adapter over the Anthropic Messages API
  (``anthropic`` SDK). It is selected automatically when ``ANTHROPIC_API_KEY`` is
  set, giving you genuinely tailored resume bullets and outreach copy.

Both satisfy the small :class:`LLMEngine` protocol, so the agents never care
which one is wired in. To use a different provider, implement ``complete`` and
pass an instance into the pipeline.
"""

from __future__ import annotations

import os
import re
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class LLMEngine(Protocol):
    """Minimal contract every engine implements."""

    name: str

    def complete(self, system: str, prompt: str, *, max_tokens: int = 512) -> str:
        """Return a completion string for the given system + user prompt."""


# ---------------------------------------------------------------------------
# Heuristic engine - no API key, fully deterministic
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "the", "and", "for", "with", "you", "our", "are", "this", "that", "will",
    "have", "from", "your", "their", "a", "an", "to", "of", "in", "on", "as",
    "we", "is", "be", "or", "at", "by", "it", "role", "team", "work", "who",
}


def keywords(text: str, limit: int = 8) -> list[str]:
    """Extract the most salient lowercase tokens from a blob of text."""
    counts: dict[str, int] = {}
    for token in re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text.lower()):
        if token in _STOPWORDS:
            continue
        counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [tok for tok, _ in ranked[:limit]]


class HeuristicEngine:
    """Template-driven engine used when no LLM key is available.

    It does not call ``complete`` for the agents (they branch on engine type for
    structured output), but it still honours the protocol so it is a drop-in.
    """

    name = "heuristic"

    def complete(self, system: str, prompt: str, *, max_tokens: int = 512) -> str:
        # Echo the most salient terms; the agents that use the heuristic engine
        # build their structured output directly rather than parsing this.
        return ", ".join(keywords(prompt, limit=6))


# ---------------------------------------------------------------------------
# Claude engine - optional, activated when ANTHROPIC_API_KEY is present
# ---------------------------------------------------------------------------

class ClaudeEngine:
    """Adapter over the Anthropic Messages API.

    Imports the ``anthropic`` SDK lazily so the package keeps working (and the
    tests keep running) when the dependency is not installed.
    """

    name = "claude"

    def __init__(self, model: str = "claude-opus-4-8", api_key: Optional[str] = None) -> None:
        try:
            import anthropic  # noqa: F401  (lazy: only needed for this engine)
        except ImportError as exc:  # pragma: no cover - exercised only without SDK
            raise RuntimeError(
                "ClaudeEngine requires the 'anthropic' package: pip install anthropic"
            ) from exc
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model

    def complete(self, system: str, prompt: str, *, max_tokens: int = 512) -> str:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in message.content if block.type == "text").strip()


def default_engine() -> LLMEngine:
    """Pick the best available engine for the current environment.

    Uses Claude when ``ANTHROPIC_API_KEY`` is set and the SDK imports cleanly;
    otherwise falls back to the deterministic heuristic engine.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return ClaudeEngine()
        except RuntimeError:
            pass
    return HeuristicEngine()
