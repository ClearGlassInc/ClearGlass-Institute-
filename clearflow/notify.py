"""Notifier seam - turn ClearFlow events into outbound signals.

The bot's value compounds when landing the keystone *tells someone*: a Slack
ping, an email draft, a calendar nudge that the next domain is now unlocked.
This module is the abstraction for that. Notifiers subscribe to the
:class:`~clearflow.events.EventBus` and render events into messages.

Three implementations ship:

* :class:`ConsoleNotifier`   - prints (the default for the CLI/demo).
* :class:`CollectingNotifier`- captures messages in memory (tests, dashboards).
* :class:`WebhookNotifier`   - POSTs JSON to a URL via ``urllib`` (stdlib only),
  the wiring point for the Slack/Zapier/Gmail MCP servers in this workspace.

Only a curated subset of event types is forwarded by default - the moments a
human cares about - so notifiers do not become noise.
"""

from __future__ import annotations

import json
import urllib.request
from abc import ABC, abstractmethod
from typing import Iterable, Optional

from clearflow.events import Event, EventBus, EventType

# The events worth interrupting a human for, by default.
DEFAULT_FORWARDED: frozenset[EventType] = frozenset({
    EventType.KEYSTONE_LANDED,
    EventType.DOMAIN_UNLOCKED,
    EventType.ITEM_BLOCKED,
    EventType.DAY_CLOSED,
})


def render(event: Event) -> str:
    """Render an event into a one-line human message."""
    p = event.payload
    if event.type == EventType.KEYSTONE_LANDED:
        return (f"🔑 Keystone landed: {p.get('action', '?')} "
                f"({p.get('domain', '?')}). The day is unlocked.")
    if event.type == EventType.DOMAIN_UNLOCKED:
        return f"🔓 Unlocked {p.get('domain', '?')}: {p.get('action', '?')}"
    if event.type == EventType.ITEM_BLOCKED:
        return f"⛔ Blocked: {p.get('action', '?')} - {p.get('reason', '')}"
    if event.type == EventType.ITEM_COMPLETED:
        return f"✅ Done: {p.get('action', '?')} ({p.get('domain', '?')})"
    if event.type == EventType.ITEM_STARTED:
        return f"▶️  Started: {p.get('action', '?')} ({p.get('domain', '?')})"
    if event.type == EventType.DAY_CLOSED:
        return (f"🌙 Day closed: {p.get('done', 0)}/{p.get('total', 0)} done, "
                f"keystone landed={p.get('keystone_landed', False)}.")
    return f"{event.type.value}: {json.dumps(p, default=str)}"


class Notifier(ABC):
    """Base class: subscribes to a bus and reacts to forwarded events."""

    def __init__(self, forward: Optional[Iterable[EventType]] = None) -> None:
        self.forward = frozenset(forward) if forward is not None else DEFAULT_FORWARDED

    def attach(self, bus: EventBus) -> "Notifier":
        """Subscribe to every event type this notifier forwards."""
        for event_type in self.forward:
            bus.subscribe(event_type, self._handle)
        return self

    def _handle(self, event: Event) -> None:
        self.deliver(event, render(event))

    @abstractmethod
    def deliver(self, event: Event, message: str) -> None:
        """Send the rendered message somewhere."""


class ConsoleNotifier(Notifier):
    """Prints messages with a tag prefix."""

    def __init__(self, prefix: str = "[clearflow]", **kw) -> None:
        super().__init__(**kw)
        self.prefix = prefix

    def deliver(self, event: Event, message: str) -> None:
        print(f"{self.prefix} {message}")


class CollectingNotifier(Notifier):
    """Stores ``(Event, message)`` pairs in memory for inspection/tests."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.messages: list[tuple[Event, str]] = []

    def deliver(self, event: Event, message: str) -> None:
        self.messages.append((event, message))

    @property
    def lines(self) -> list[str]:
        return [m for _, m in self.messages]


class WebhookNotifier(Notifier):
    """POSTs event JSON to a URL (Slack-incoming-webhook compatible shape).

    Uses ``urllib`` so it needs no third-party HTTP client. Network failures are
    swallowed and counted on :attr:`failures` - a notifier must never break the
    workflow that emitted the event.
    """

    def __init__(self, url: str, *, timeout: float = 5.0, **kw) -> None:
        super().__init__(**kw)
        self.url = url
        self.timeout = timeout
        self.sent = 0
        self.failures: list[str] = []

    def deliver(self, event: Event, message: str) -> None:
        body = json.dumps({
            "text": message,
            "event": event.to_dict(),
        }).encode("utf-8")
        request = urllib.request.Request(
            self.url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                resp.read()
            self.sent += 1
        except Exception as exc:  # noqa: BLE001 - delivery is best-effort
            self.failures.append(f"{type(exc).__name__}: {exc}")


class DigestNotifier(Notifier):
    """Accumulates the day's events into one email-ready digest.

    Unlike the streaming notifiers above, this one is a *batcher*: it captures
    every lifecycle event (not just the interrupt-worthy subset) and renders a
    single subject + body at close-out. Anything that can send text - the Gmail
    connector, a Zapier email action, ``sendmail`` - can consume the result, so
    this is the seam between the in-process bus and mail/automation providers.
    """

    def __init__(self, *, subject_prefix: str = "[ClearFlow]", **kw) -> None:
        # Capture the full event stream by default; the digest is the record.
        kw.setdefault("forward", frozenset(EventType))
        super().__init__(**kw)
        self.subject_prefix = subject_prefix
        self.entries: list[tuple[Event, str]] = []

    def deliver(self, event: Event, message: str) -> None:
        self.entries.append((event, message))

    @property
    def keystone_landed(self) -> bool:
        return any(e.type == EventType.KEYSTONE_LANDED for e, _ in self.entries)

    def render(self) -> dict[str, str]:
        """Render ``{"subject": ..., "body": ...}`` for a mail/automation hook."""
        landed = self.keystone_landed
        unlocked = [e.payload.get("domain", "?") for e, _ in self.entries
                    if e.type == EventType.DOMAIN_UNLOCKED]
        done = sum(1 for e, _ in self.entries
                   if e.type == EventType.ITEM_COMPLETED)
        subject = (f"{self.subject_prefix} Keystone landed - "
                   f"{done} done, unlocked: {', '.join(unlocked) or 'none'}"
                   if landed else
                   f"{self.subject_prefix} Day report - keystone still open "
                   f"({done} done)")
        lines = ["ClearFlow daily digest", "=" * 40]
        for event, message in self.entries:
            stamp = event.at.strftime("%H:%M:%S")
            lines.append(f"{stamp}  {event.type.value:<18} {message}")
        lines.append("=" * 40)
        lines.append(f"keystone landed: {landed} | items completed: {done} | "
                     f"domains unlocked: {', '.join(unlocked) or 'none'}")
        return {"subject": subject, "body": "\n".join(lines)}
