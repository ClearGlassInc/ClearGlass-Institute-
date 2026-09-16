"""ClearFlow event bus - the nervous system the orchestrator emits into.

Every meaningful state change in :class:`~clearflow.workflow.AutomationWorkflow`
(an item starts, a keystone lands, a domain unlocks, the day closes) is published
here as a typed :class:`Event`. Subscribers - notifiers, the history store, an
async runner, a future WebSocket fan-out - react without the workflow knowing who
is listening.

Design notes:

* Synchronous, in-process, ordered delivery. A distributed deployment swaps this
  for Redis pub/sub or a message broker behind the same ``emit``/``subscribe``
  seam.
* Handler errors are isolated: one bad subscriber never breaks the emit path or
  starves the others. Failures are captured on :attr:`EventBus.dead_letters` for
  inspection rather than raised.
* ``subscribe(None, handler)`` registers a wildcard handler that sees every
  event - the hook the history store and audit log use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from clearflow.models import new_trace_id, utcnow


class EventType(str, Enum):
    """Every published lifecycle moment in a ClearFlow day."""

    DAY_OPENED = "day.opened"
    BRIEF_INGESTED = "brief.ingested"
    COMMITMENTS_SET = "commitments.set"
    ITEM_STARTED = "item.started"
    ITEM_COMPLETED = "item.completed"
    ITEM_BLOCKED = "item.blocked"
    DOMAIN_UNLOCKED = "domain.unlocked"
    KEYSTONE_LANDED = "keystone.landed"
    DAY_CLOSED = "day.closed"


@dataclass
class Event:
    """An immutable record of something that happened, with a payload."""

    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=new_trace_id)
    at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "type": self.type.value,
            "payload": self.payload,
            "at": self.at.isoformat(),
        }


Handler = Callable[[Event], None]


@dataclass
class _DeadLetter:
    event: Event
    handler: str
    error: str


class EventBus:
    """A tiny synchronous, fault-isolating publish/subscribe bus."""

    def __init__(self) -> None:
        # Per-type subscribers plus a wildcard bucket keyed by ``None``.
        self._subscribers: dict[Optional[EventType], list[Handler]] = {}
        self.log: list[Event] = []
        self.dead_letters: list[_DeadLetter] = []

    def subscribe(self, event_type: Optional[EventType], handler: Handler) -> Handler:
        """Register ``handler`` for ``event_type`` (or all events if ``None``).

        Returns the handler so it can be used as a decorator and later passed to
        :meth:`unsubscribe`.
        """
        self._subscribers.setdefault(event_type, []).append(handler)
        return handler

    def on(self, event_type: Optional[EventType] = None) -> Callable[[Handler], Handler]:
        """Decorator form of :meth:`subscribe`."""
        def decorator(handler: Handler) -> Handler:
            return self.subscribe(event_type, handler)
        return decorator

    def unsubscribe(self, event_type: Optional[EventType], handler: Handler) -> bool:
        """Remove a previously registered handler; returns True if found."""
        bucket = self._subscribers.get(event_type, [])
        if handler in bucket:
            bucket.remove(handler)
            return True
        return False

    def emit(self, event_type: EventType, **payload: Any) -> Event:
        """Publish an event to type-specific and wildcard subscribers.

        Delivery order is deterministic: specific subscribers first (in
        registration order), then wildcard subscribers. The event is appended to
        :attr:`log` regardless of subscriber count, so the bus doubles as an
        ordered audit trail.
        """
        event = Event(type=event_type, payload=dict(payload))
        self.log.append(event)
        for handler in list(self._subscribers.get(event_type, [])):
            self._dispatch(handler, event)
        for handler in list(self._subscribers.get(None, [])):
            self._dispatch(handler, event)
        return event

    def _dispatch(self, handler: Handler, event: Event) -> None:
        try:
            handler(event)
        except Exception as exc:  # noqa: BLE001 - isolation is the whole point
            self.dead_letters.append(_DeadLetter(
                event=event,
                handler=getattr(handler, "__qualname__", repr(handler)),
                error=f"{type(exc).__name__}: {exc}",
            ))

    def events_of(self, event_type: EventType) -> list[Event]:
        """All logged events of a given type (handy in tests and replays)."""
        return [e for e in self.log if e.type == event_type]
