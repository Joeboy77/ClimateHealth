from datetime import datetime
from enum import StrEnum

from climahealth.services.models import ServiceModel


class EventType(StrEnum):
    DISTRICT_CONDITIONS_CHANGED = "district_conditions_changed"
    INCIDENT_ACTION_UPDATED = "incident_action_updated"
    REPORT_SUBMITTED = "report_submitted"
    SHIELD_CHANGED = "shield_changed"


class DomainEvent(ServiceModel):
    event_type: EventType
    district_id: str
    resource_id: str | None
    summary: str
    occurred_at: datetime


class NullEventPublisher:
    def publish(self, event: DomainEvent) -> None:
        return None
