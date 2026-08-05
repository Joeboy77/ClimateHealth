from datetime import date, datetime
from itertools import count

from climahealth.services.access import Agency, AuthenticatedUser
from climahealth.services.incident_service import (
    ActionOrigin,
    ActionStatus,
    ActionTransition,
    IncidentAction,
    IncidentActionAssignment,
)
from climahealth.services.stock import ResourceStock

SEEDED_ACTIONS: tuple[IncidentAction, ...] = (
    IncidentAction(
        action_id="madina-1",
        district_id="madina",
        agency=Agency.GHANA_HEALTH_SERVICE,
        description="Pre-position rapid diagnostic tests at all sub-district facilities",
        status=ActionStatus.IN_PROGRESS,
        due_on=date(2026, 8, 5),
        assigned_by="Akosua Mensah",
        assigned_by_role="National Surveillance Officer, GHS",
        assigned_on=date(2026, 8, 1),
        location_name="Madina Polyclinic",
        latitude=5.6835,
        longitude=-0.1662,
    ),
    IncidentAction(
        action_id="madina-2",
        district_id="madina",
        agency=Agency.DISTRICT_ASSEMBLY,
        description="Clear blocked drains in flood-prone zones",
        status=ActionStatus.NOT_STARTED,
        due_on=date(2026, 8, 8),
        assigned_by="Akosua Mensah",
        assigned_by_role="National Surveillance Officer, GHS",
        assigned_on=date(2026, 8, 1),
        location_name="Madina Market storm drain",
        latitude=5.6849,
        longitude=-0.1673,
    ),
    IncidentAction(
        action_id="madina-3",
        district_id="madina",
        agency=Agency.GHANA_HEALTH_SERVICE,
        description="House-to-house net inspection in three communities",
        status=ActionStatus.NOT_STARTED,
        due_on=date(2026, 8, 12),
        assigned_by="Akosua Mensah",
        assigned_by_role="National Surveillance Officer, GHS",
        assigned_on=date(2026, 8, 1),
        location_name="Zongo Junction",
        latitude=5.7180,
        longitude=-0.1585,
    ),
    IncidentAction(
        action_id="wa-1",
        district_id="wa",
        agency=Agency.GHANA_HEALTH_SERVICE,
        description="Confirm meningitis vaccine cold-chain capacity",
        status=ActionStatus.COMPLETE,
        due_on=date(2026, 8, 2),
        assigned_by="Akosua Mensah",
        assigned_by_role="National Surveillance Officer, GHS",
        assigned_on=date(2026, 8, 1),
        location_name="Wa Regional Hospital",
        latitude=10.0601,
        longitude=-2.5057,
    ),
    IncidentAction(
        action_id="wa-2",
        district_id="wa",
        agency=Agency.GHANA_HEALTH_SERVICE,
        description="Brief clinicians on meningitis case definitions",
        status=ActionStatus.IN_PROGRESS,
        due_on=date(2026, 8, 6),
        assigned_by="Akosua Mensah",
        assigned_by_role="National Surveillance Officer, GHS",
        assigned_on=date(2026, 8, 1),
        location_name="Regional Health Directorate",
        latitude=10.0440,
        longitude=-2.4880,
    ),
    IncidentAction(
        action_id="wa-3",
        district_id="wa",
        agency=Agency.NADMO,
        description="Broadcast harmattan dust advisory on local radio",
        status=ActionStatus.BLOCKED,
        due_on=date(2026, 8, 4),
        assigned_by="Akosua Mensah",
        assigned_by_role="National Surveillance Officer, GHS",
        assigned_on=date(2026, 8, 1),
        location_name="Radio Upper West, Wa",
        latitude=10.0700,
        longitude=-2.4700,
    ),
)

SEEDED_STOCKS: tuple[ResourceStock, ...] = (
    ResourceStock(
        district_id="madina",
        resource="Rapid diagnostic tests",
        baseline_units=500,
        stocked_units=900,
    ),
    ResourceStock(
        district_id="madina",
        resource="Artemisinin combination therapy",
        baseline_units=400,
        stocked_units=260,
    ),
    ResourceStock(
        district_id="madina",
        resource="Oral rehydration salts",
        baseline_units=300,
        stocked_units=110,
    ),
    ResourceStock(
        district_id="wa",
        resource="Meningitis vaccine doses",
        baseline_units=600,
        stocked_units=420,
    ),
    ResourceStock(
        district_id="wa",
        resource="Ceftriaxone vials",
        baseline_units=200,
        stocked_units=60,
    ),
    ResourceStock(
        district_id="wa",
        resource="Oral rehydration salts",
        baseline_units=250,
        stocked_units=240,
    ),
)


class InMemoryIncidentActionStore:
    def __init__(self, actions: tuple[IncidentAction, ...] | None = None) -> None:
        resolved = actions if actions is not None else SEEDED_ACTIONS
        self._actions = {action.action_id: action for action in resolved}
        self._sequence = count(len(self._actions) + 1)

    def all_actions(self) -> tuple[IncidentAction, ...]:
        return tuple(self._actions.values())

    def for_district(self, district_id: str) -> tuple[IncidentAction, ...]:
        return tuple(
            action for action in self._actions.values() if action.district_id == district_id
        )

    def find(self, district_id: str, action_id: str) -> IncidentAction | None:
        action = self._actions.get(action_id)
        if action is None or action.district_id != district_id:
            return None
        return action

    def update_status(
        self,
        district_id: str,
        action_id: str,
        status: ActionStatus,
        actor: AuthenticatedUser,
        at: datetime,
    ) -> IncidentAction | None:
        action = self.find(district_id, action_id)
        if action is None:
            return None
        updated = action.model_copy(
            update={
                "status": status,
                "updated_by": actor.display_name,
                "updated_by_agency": actor.agency,
                "updated_at": at,
            }
        )
        self._actions[action_id] = updated
        return updated

    def add(
        self,
        district_id: str,
        assignment: IncidentActionAssignment,
        actor: AuthenticatedUser,
        assigned_on: date,
    ) -> IncidentAction:
        action = IncidentAction(
            action_id=f"{district_id}-{next(self._sequence)}",
            district_id=district_id,
            agency=assignment.agency,
            description=assignment.description,
            status=ActionStatus.NOT_STARTED,
            due_on=assignment.due_on,
            assigned_by=actor.display_name,
            assigned_by_role=f"{actor.job_title}, {actor.agency_short_name}",
            assigned_on=assigned_on,
            location_name=assignment.location_name,
            latitude=assignment.latitude,
            longitude=assignment.longitude,
        )
        self._actions[action.action_id] = action
        return action

    def add_playbook_action(
        self,
        action_id: str,
        district_id: str,
        agency: Agency,
        description: str,
        source_condition: str,
        is_lead: bool,
        due_on: date,
        assigned_on: date,
    ) -> IncidentAction:
        action = IncidentAction(
            action_id=action_id,
            district_id=district_id,
            agency=agency,
            origin=ActionOrigin.PLAYBOOK,
            source_condition=source_condition,
            is_lead=is_lead,
            description=description,
            status=ActionStatus.NOT_STARTED,
            due_on=due_on,
            assigned_by="ClimaHealth playbook",
            assigned_by_role="Standing agency mandate",
            assigned_on=assigned_on,
        )
        self._actions[action_id] = action
        return action


class InMemoryResourceStockStore:
    def __init__(self, stocks: tuple[ResourceStock, ...] = SEEDED_STOCKS) -> None:
        self._stocks = stocks

    def for_district(self, district_id: str) -> tuple[ResourceStock, ...]:
        return tuple(stock for stock in self._stocks if stock.district_id == district_id)


class ReportIdentifierSequence:
    def __init__(self, prefix: str = "report") -> None:
        self._prefix = prefix
        self._counter = count(1)

    def next_identifier(self) -> str:
        return f"{self._prefix}-{next(self._counter)}"


class InMemoryActionTransitionStore:
    """Append-only history. `record` only ever appends; nothing mutates or deletes."""

    def __init__(self) -> None:
        self._transitions: list[ActionTransition] = []

    def record(self, transition: ActionTransition) -> None:
        self._transitions.append(transition)

    def for_action(self, action_id: str) -> tuple[ActionTransition, ...]:
        return tuple(
            transition for transition in self._transitions if transition.action_id == action_id
        )

    def for_district(self, district_id: str) -> tuple[ActionTransition, ...]:
        return tuple(
            transition for transition in self._transitions if transition.district_id == district_id
        )
