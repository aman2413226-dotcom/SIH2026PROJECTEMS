import asyncio
from typing import Callable, Dict, List, Coroutine, Any
from backend.app.events.events import StationEvent
from backend.app.core.logger import logger


class EventBus:
    """
    Lightweight asynchronous publish-subscribe event bus for real-time
    microgrid alerts, autonomous diesel dispatch triggers, and blizzard warnings.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[StationEvent], Coroutine[Any, Any, None]]]] = {}
        self._history: List[StationEvent] = []
        self._max_history = 100

    def subscribe(self, event_type: str, handler: Callable[[StationEvent], Coroutine[Any, Any, None]]) -> None:
        """Register an async handler for a given event type or '*' for all events."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Registered subscriber for event type: {event_type}")

    async def publish(self, event: StationEvent) -> None:
        """Publish an event to all matching subscribers asynchronously."""
        # Store in bounded circular history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        logger.info(f"EventBus published [{event.severity}] {event.event_type}: {event.message}")

        handlers = list(self._subscribers.get(event.event_type, []))
        # Include wildcard handlers
        handlers.extend(self._subscribers.get("*", []))

        if handlers:
            tasks = [asyncio.create_task(h(event)) for h in handlers]
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_recent_events(self, limit: int = 20) -> List[StationEvent]:
        """Returns most recent events recorded on the bus."""
        return self._history[-limit:]


# Global singleton event bus
event_bus = EventBus()

