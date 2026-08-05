from queue import Empty, SimpleQueue

from climahealth.services.access import Scope
from climahealth.services.events import DomainEvent


class EventSubscription:
    def __init__(self, scope: Scope) -> None:
        self._scope = scope
        self._pending: SimpleQueue[DomainEvent] = SimpleQueue()

    def offer(self, event: DomainEvent) -> bool:
        if not self._scope.permits(event.district_id):
            return False
        self._pending.put(event)
        return True

    def drain(self) -> tuple[DomainEvent, ...]:
        events: list[DomainEvent] = []
        while True:
            try:
                events.append(self._pending.get_nowait())
            except Empty:
                return tuple(events)


class InMemoryEventBroadcaster:
    def __init__(self) -> None:
        self._subscriptions: list[EventSubscription] = []

    def subscribe(self, scope: Scope) -> EventSubscription:
        subscription = EventSubscription(scope)
        self._subscriptions.append(subscription)
        return subscription

    def unsubscribe(self, subscription: EventSubscription) -> None:
        if subscription in self._subscriptions:
            self._subscriptions.remove(subscription)

    def publish(self, event: DomainEvent) -> None:
        for subscription in tuple(self._subscriptions):
            subscription.offer(event)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscriptions)
