from datetime import UTC, date, datetime, timedelta
from enum import StrEnum

from pydantic import Field

from climahealth.domain.models import RiskLevel
from climahealth.services.access import (
    AGENCY_NAMES,
    AGENCY_SHORT_NAMES,
    ActionNotAssignedToYou,
    Agency,
    AuthenticatedUser,
    NotACoordinator,
)
from climahealth.services.events import DomainEvent, EventType, NullEventPublisher
from climahealth.services.models import District, ServiceModel
from climahealth.services.playbook import responsibilities_for
from climahealth.services.ports import (
    ActionTransitionStore,
    Clock,
    EventPublisher,
    IncidentActionStore,
)
from climahealth.services.risk_service import DistrictRiskReport, RiskService


class ActionOrigin(StrEnum):
    PLAYBOOK = "playbook"
    ASSIGNED = "assigned"


class ActionStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    BLOCKED = "blocked"


class ReadinessStatus(StrEnum):
    """How a district's stock stands against what the forecast will demand.

    Emergency is separated from critical because they call for different actions:
    critical means order more, emergency means the shortfall lands before the
    cases do and somebody has to move stock today.
    """

    READY = "ready"
    STRETCHED = "stretched"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ActionTransition(ServiceModel):
    """One immutable entry in an action's history. Never edited, never removed."""

    action_id: str
    district_id: str
    from_status: ActionStatus | None
    to_status: ActionStatus
    actor_name: str
    actor_agency: Agency
    actor_role: str
    occurred_at: datetime


class IncidentAction(ServiceModel):
    action_id: str
    district_id: str
    agency: Agency
    origin: ActionOrigin = ActionOrigin.ASSIGNED
    source_condition: str | None = None
    is_lead: bool = False
    description: str
    status: ActionStatus
    due_on: date
    assigned_by: str
    assigned_by_role: str
    assigned_on: date
    updated_by: str | None = None
    updated_by_agency: Agency | None = None
    updated_at: datetime | None = None
    location_name: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @property
    def agency_name(self) -> str:
        return AGENCY_NAMES[self.agency]

    @property
    def agency_short_name(self) -> str:
        return AGENCY_SHORT_NAMES[self.agency]


class IncidentActionUpdate(ServiceModel):
    action_id: str
    status: ActionStatus


class IncidentActionAssignment(ServiceModel):
    agency: Agency
    description: str = Field(min_length=1, max_length=300)
    due_on: date
    location_name: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class IncidentRoom(ServiceModel):
    district_id: str
    district_name: str
    overall_risk_level: RiskLevel
    generated_on: date
    actions: tuple[IncidentAction, ...]
    history: tuple[ActionTransition, ...] = ()


class ResourceReadiness(ServiceModel):
    resource: str
    required_units: int = Field(ge=0)
    stocked_units: int = Field(ge=0)
    status: ReadinessStatus
    shortfall_units: int = Field(ge=0)
    hours_to_dispatch: int | None = None


class ReadinessReport(ServiceModel):
    district_id: str
    district_name: str
    overall_risk_level: RiskLevel
    generated_on: date
    open_reports: int = Field(ge=0)
    resources: tuple[ResourceReadiness, ...]
    status: ReadinessStatus
    hours_to_dispatch: int | None = None


class UnknownIncidentAction(LookupError):
    pass


PLAYBOOK_TRIGGER_LEVELS: frozenset[RiskLevel] = frozenset({RiskLevel.HIGH, RiskLevel.SEVERE})


def playbook_action_id(district_id: str, condition: str, agency: Agency) -> str:
    return f"{district_id}:{condition}:{agency.value}"


READINESS_STRETCHED_RATIO = 0.75
READINESS_CRITICAL_RATIO = 0.4
READINESS_EMERGENCY_RATIO = 0.2
HOURS_PER_DAY = 24

RISK_DEMAND_MULTIPLIER: dict[RiskLevel, float] = {
    RiskLevel.LOW: 0.5,
    RiskLevel.MODERATE: 1.0,
    RiskLevel.HIGH: 1.5,
    RiskLevel.SEVERE: 2.0,
}

READINESS_SEVERITY: tuple[ReadinessStatus, ...] = (
    ReadinessStatus.READY,
    ReadinessStatus.STRETCHED,
    ReadinessStatus.CRITICAL,
    ReadinessStatus.EMERGENCY,
)


def readiness_status(required_units: int, stocked_units: int) -> ReadinessStatus:
    if required_units == 0:
        return ReadinessStatus.READY
    coverage = stocked_units / required_units
    if coverage >= READINESS_STRETCHED_RATIO:
        return ReadinessStatus.READY
    if coverage < READINESS_EMERGENCY_RATIO:
        return ReadinessStatus.EMERGENCY
    if coverage >= READINESS_CRITICAL_RATIO:
        return ReadinessStatus.STRETCHED
    return ReadinessStatus.CRITICAL


def hours_to_dispatch(shortfall_units: int, earliest_onset_days: int) -> int | None:
    """How long there is to move stock before the cases arrive.

    The onset window is the deadline: a shortfall does not matter in the
    abstract, it matters against the date the ward fills up.
    """
    if shortfall_units <= 0:
        return None
    return max(earliest_onset_days, 0) * HOURS_PER_DAY


def worst_status(statuses: tuple[ReadinessStatus, ...]) -> ReadinessStatus:
    if not statuses:
        return ReadinessStatus.READY
    return max(statuses, key=READINESS_SEVERITY.index)


def required_units_for(baseline_units: int, level: RiskLevel) -> int:
    return round(baseline_units * RISK_DEMAND_MULTIPLIER[level])


class IncidentService:
    def __init__(
        self,
        risk_service: RiskService,
        actions: IncidentActionStore,
        transitions: ActionTransitionStore,
        clock: Clock,
        events: EventPublisher | None = None,
    ) -> None:
        self._risk_service = risk_service
        self._actions = actions
        self._transitions = transitions
        self._clock = clock
        self._events = events or NullEventPublisher()

    def incident_room(self, district: District) -> IncidentRoom:
        report = self._risk_service.report_for(district)
        self._synchronise_playbook(district, report)
        return IncidentRoom(
            district_id=district.district_id,
            district_name=district.name,
            overall_risk_level=report.overall_level,
            generated_on=report.generated_on,
            actions=self._actions.for_district(district.district_id),
            history=self._transitions.for_district(district.district_id),
        )

    def _synchronise_playbook(self, district: District, report: DistrictRiskReport) -> None:
        """Turn the engine's raised conditions into each agency's standing task.

        No coordinator is involved. A condition crossing the alert threshold is
        itself the instruction, so every agency with a mandate for that condition
        finds its task waiting. Ids are derived, so a task keeps its status and
        history across recomputation.
        """
        for risk in report.risks:
            if risk.level not in PLAYBOOK_TRIGGER_LEVELS:
                continue
            for responsibility in responsibilities_for(risk.condition):
                action_id = playbook_action_id(
                    district.district_id, risk.condition.value, responsibility.agency
                )
                if self._actions.find(district.district_id, action_id) is not None:
                    continue
                self._actions.add_playbook_action(
                    action_id=action_id,
                    district_id=district.district_id,
                    agency=responsibility.agency,
                    description=responsibility.task,
                    source_condition=risk.condition.value,
                    is_lead=responsibility.is_lead,
                    due_on=self._clock.today()
                    + timedelta(days=max(risk.lag_window.minimum_days, 1)),
                    assigned_on=self._clock.today(),
                )

    def national_actions(self, districts: tuple[District, ...]) -> tuple[IncidentAction, ...]:
        """Every assigned action across the districts a coordinator can see."""
        visible = {district.district_id for district in districts}
        return tuple(
            action for action in self._actions.all_actions() if action.district_id in visible
        )

    def update_action(
        self,
        district: District,
        update: IncidentActionUpdate,
        actor: AuthenticatedUser,
    ) -> IncidentAction:
        existing = self._actions.find(district.district_id, update.action_id)
        if existing is None:
            raise UnknownIncidentAction(
                f"No action '{update.action_id}' in district '{district.district_id}'"
            )
        if not actor.may_update_action_of(existing.agency):
            raise ActionNotAssignedToYou(AGENCY_NAMES[existing.agency])

        updated = self._actions.update_status(
            district.district_id,
            update.action_id,
            update.status,
            actor=actor,
            at=datetime.now(UTC),
        )
        if updated is None:
            raise UnknownIncidentAction(
                f"No action '{update.action_id}' in district '{district.district_id}'"
            )

        self._transitions.record(
            ActionTransition(
                action_id=updated.action_id,
                district_id=district.district_id,
                from_status=existing.status,
                to_status=updated.status,
                actor_name=actor.display_name,
                actor_agency=actor.agency,
                actor_role=actor.role_name,
                occurred_at=updated.updated_at or datetime.now(UTC),
            )
        )
        self._events.publish(
            DomainEvent(
                event_type=EventType.INCIDENT_ACTION_UPDATED,
                district_id=district.district_id,
                resource_id=updated.action_id,
                summary=(
                    f"{AGENCY_SHORT_NAMES[updated.agency]} action moved to "
                    f"{updated.status.value.replace('_', ' ')} by {actor.display_name}"
                ),
                occurred_at=datetime.now(UTC),
            )
        )
        return updated

    def history_for(self, district: District, action_id: str) -> tuple[ActionTransition, ...]:
        return self._transitions.for_action(action_id)

    def assign_action(
        self,
        district: District,
        assignment: IncidentActionAssignment,
        actor: AuthenticatedUser,
    ) -> IncidentAction:
        """Only a coordinator may create work for an agency."""
        if not actor.coordinates_response:
            raise NotACoordinator()

        created = self._actions.add(
            district_id=district.district_id,
            assignment=assignment,
            actor=actor,
            assigned_on=self._clock.today(),
        )
        self._events.publish(
            DomainEvent(
                event_type=EventType.INCIDENT_ACTION_UPDATED,
                district_id=district.district_id,
                resource_id=created.action_id,
                summary=(
                    f"{actor.display_name} assigned "
                    f"{AGENCY_SHORT_NAMES[created.agency]} a new action"
                ),
                occurred_at=datetime.now(UTC),
            )
        )
        return created
