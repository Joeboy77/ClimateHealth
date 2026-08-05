from datetime import UTC, datetime

from climahealth.infrastructure.events.broadcaster import InMemoryEventBroadcaster
from climahealth.services.access import district_scope, national_scope
from climahealth.services.events import DomainEvent, EventType, NullEventPublisher


def event_for(district_id: str, summary: str = "something happened") -> DomainEvent:
    return DomainEvent(
        event_type=EventType.REPORT_SUBMITTED,
        district_id=district_id,
        resource_id="report-1",
        summary=summary,
        occurred_at=datetime(2026, 7, 27, 9, 30, tzinfo=UTC),
    )


def test_a_national_subscriber_receives_every_district():
    broadcaster = InMemoryEventBroadcaster()
    subscription = broadcaster.subscribe(national_scope())

    broadcaster.publish(event_for("madina"))
    broadcaster.publish(event_for("wa"))

    assert [event.district_id for event in subscription.drain()] == ["madina", "wa"]


def test_a_district_subscriber_receives_only_its_own_district():
    broadcaster = InMemoryEventBroadcaster()
    subscription = broadcaster.subscribe(district_scope("madina"))

    broadcaster.publish(event_for("madina"))
    broadcaster.publish(event_for("wa"))

    assert [event.district_id for event in subscription.drain()] == ["madina"]


def test_draining_twice_does_not_repeat_events():
    broadcaster = InMemoryEventBroadcaster()
    subscription = broadcaster.subscribe(national_scope())
    broadcaster.publish(event_for("madina"))

    subscription.drain()

    assert subscription.drain() == ()


def test_events_are_delivered_to_every_subscriber():
    broadcaster = InMemoryEventBroadcaster()
    first = broadcaster.subscribe(national_scope())
    second = broadcaster.subscribe(national_scope())

    broadcaster.publish(event_for("madina"))

    assert len(first.drain()) == 1
    assert len(second.drain()) == 1


def test_unsubscribing_stops_delivery():
    broadcaster = InMemoryEventBroadcaster()
    subscription = broadcaster.subscribe(national_scope())

    broadcaster.unsubscribe(subscription)
    broadcaster.publish(event_for("madina"))

    assert subscription.drain() == ()
    assert broadcaster.subscriber_count == 0


def test_unsubscribing_twice_is_harmless():
    broadcaster = InMemoryEventBroadcaster()
    subscription = broadcaster.subscribe(national_scope())

    broadcaster.unsubscribe(subscription)
    broadcaster.unsubscribe(subscription)

    assert broadcaster.subscriber_count == 0


def test_publishing_with_no_subscribers_is_harmless():
    InMemoryEventBroadcaster().publish(event_for("madina"))


def test_the_null_publisher_swallows_events():
    assert NullEventPublisher().publish(event_for("madina")) is None


def test_events_preserve_their_order():
    broadcaster = InMemoryEventBroadcaster()
    subscription = broadcaster.subscribe(national_scope())

    for index in range(5):
        broadcaster.publish(event_for("madina", summary=f"event {index}"))

    assert [event.summary for event in subscription.drain()] == [
        f"event {index}" for index in range(5)
    ]
