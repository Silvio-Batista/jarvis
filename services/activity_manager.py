from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from collections import deque


@dataclass
class ActivityEvent:
    timestamp: datetime
    source: str
    message: str
    level: str = "info"  # info | success | warn | error | jarvis | user | system

    def time_str(self) -> str:
        return self.timestamp.strftime("%H:%M:%S")


class ActivityManager:
    def __init__(self, maxlen: int = 40) -> None:
        self._events: deque[ActivityEvent] = deque(maxlen=maxlen)

    def add(self, source: str, message: str, level: str = "info") -> ActivityEvent:
        event = ActivityEvent(
            timestamp=datetime.now(),
            source=source.upper(),
            message=message,
            level=level,
        )
        self._events.appendleft(event)
        return event

    def all(self) -> list[ActivityEvent]:
        return list(self._events)
