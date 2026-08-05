from datetime import date, datetime

from climahealth.api.schemas.common import ApiModel
from climahealth.domain.models import RiskLevel
from climahealth.services.access import Agency
from climahealth.services.action_urgency import (
    ActionUrgency,
    hours_since_movement,
    urgency_for,
)
from climahealth.services.incident_service import (
    ActionOrigin,
    ActionStatus,
    ActionTransition,
    IncidentAction,
    IncidentRoom,
)


class ActionTransitionResponse(ApiModel):
    action_id: str
    from_status: ActionStatus | None
    to_status: ActionStatus
    actor_name: str
    actor_agency: Agency
    actor_role: str
    occurred_at: datetime

    @classmethod
    def of(cls, transition: ActionTransition) -> "ActionTransitionResponse":
        return cls(
            action_id=transition.action_id,
            from_status=transition.from_status,
            to_status=transition.to_status,
            actor_name=transition.actor_name,
            actor_agency=transition.actor_agency,
            actor_role=transition.actor_role,
            occurred_at=transition.occurred_at,
        )


class IncidentActionResponse(ApiModel):
    action_id: str
    district_id: str
    agency: Agency
    origin: ActionOrigin
    source_condition: str | None
    is_lead: bool
    agency_name: str
    agency_short_name: str
    description: str
    status: ActionStatus
    due_on: date
    assigned_by: str
    assigned_by_role: str
    assigned_on: date
    updated_by: str | None
    updated_by_agency: Agency | None
    updated_at: datetime | None
    location_name: str | None
    latitude: float | None
    longitude: float | None
    urgency: ActionUrgency
    hours_since_movement: float

    @classmethod
    def of(cls, action: IncidentAction, now: datetime) -> "IncidentActionResponse":
        return cls(
            urgency=urgency_for(action, now),
            hours_since_movement=round(hours_since_movement(action, now), 1),
            action_id=action.action_id,
            district_id=action.district_id,
            agency=action.agency,
            origin=action.origin,
            source_condition=action.source_condition,
            is_lead=action.is_lead,
            agency_name=action.agency_name,
            agency_short_name=action.agency_short_name,
            description=action.description,
            status=action.status,
            due_on=action.due_on,
            assigned_by=action.assigned_by,
            assigned_by_role=action.assigned_by_role,
            assigned_on=action.assigned_on,
            updated_by=action.updated_by,
            updated_by_agency=action.updated_by_agency,
            updated_at=action.updated_at,
            location_name=action.location_name,
            latitude=action.latitude,
            longitude=action.longitude,
        )


class IncidentRoomResponse(ApiModel):
    district_id: str
    district_name: str
    overall_risk_level: RiskLevel
    generated_on: date
    actions: list[IncidentActionResponse]
    history: list[ActionTransitionResponse]

    @classmethod
    def of(cls, room: IncidentRoom, now: datetime) -> "IncidentRoomResponse":
        return cls(
            district_id=room.district_id,
            district_name=room.district_name,
            overall_risk_level=room.overall_risk_level,
            generated_on=room.generated_on,
            actions=[IncidentActionResponse.of(action, now) for action in room.actions],
            history=[ActionTransitionResponse.of(transition) for transition in room.history],
        )
