from datetime import date, datetime
from itertools import count

from sqlalchemy import select

from climahealth.infrastructure.database.engine import SessionFactory
from climahealth.infrastructure.database.tables import (
    ActionTransitionRow,
    IncidentActionRow,
)
from climahealth.services.access import Agency, AuthenticatedUser
from climahealth.services.incident_service import (
    ActionOrigin,
    ActionStatus,
    ActionTransition,
    IncidentAction,
    IncidentActionAssignment,
)


def _to_action(row: IncidentActionRow) -> IncidentAction:
    return IncidentAction(
        action_id=row.action_id,
        district_id=row.district_id,
        agency=Agency(row.agency),
        origin=ActionOrigin(row.origin),
        source_condition=row.source_condition,
        is_lead=row.is_lead,
        description=row.description,
        status=ActionStatus(row.status),
        due_on=row.due_on,
        assigned_by=row.assigned_by,
        assigned_by_role=row.assigned_by_role,
        assigned_on=row.assigned_on,
        updated_by=row.updated_by,
        updated_by_agency=(Agency(row.updated_by_agency) if row.updated_by_agency else None),
        updated_at=row.updated_at,
        location_name=row.location_name,
        latitude=row.latitude,
        longitude=row.longitude,
    )


class PostgresIncidentActionStore:
    def __init__(self, sessions: SessionFactory) -> None:
        self._sessions = sessions
        self._sequence = count(1)

    def seed(self, actions: tuple[IncidentAction, ...]) -> None:
        """Insert the demonstration actions once, leaving existing rows untouched."""
        with self._sessions.begin() as session:
            existing = set(session.scalars(select(IncidentActionRow.action_id)))
            for action in actions:
                if action.action_id in existing:
                    continue
                session.add(
                    IncidentActionRow(
                        action_id=action.action_id,
                        district_id=action.district_id,
                        agency=action.agency.value,
                        origin=action.origin.value,
                        source_condition=action.source_condition,
                        is_lead=action.is_lead,
                        description=action.description,
                        status=action.status.value,
                        due_on=action.due_on,
                        assigned_by=action.assigned_by,
                        assigned_by_role=action.assigned_by_role,
                        assigned_on=action.assigned_on,
                        location_name=action.location_name,
                        latitude=action.latitude,
                        longitude=action.longitude,
                    )
                )

    def all_actions(self) -> tuple[IncidentAction, ...]:
        with self._sessions.begin() as session:
            rows = session.scalars(select(IncidentActionRow)).all()
            return tuple(_to_action(row) for row in rows)

    def for_district(self, district_id: str) -> tuple[IncidentAction, ...]:
        with self._sessions.begin() as session:
            rows = session.scalars(
                select(IncidentActionRow).where(IncidentActionRow.district_id == district_id)
            ).all()
            return tuple(_to_action(row) for row in rows)

    def find(self, district_id: str, action_id: str) -> IncidentAction | None:
        with self._sessions.begin() as session:
            row = session.get(IncidentActionRow, action_id)
            if row is None or row.district_id != district_id:
                return None
            return _to_action(row)

    def update_status(
        self,
        district_id: str,
        action_id: str,
        status: ActionStatus,
        actor: AuthenticatedUser,
        at: datetime,
    ) -> IncidentAction | None:
        with self._sessions.begin() as session:
            row = session.get(IncidentActionRow, action_id)
            if row is None or row.district_id != district_id:
                return None
            row.status = status.value
            row.updated_by = actor.display_name
            row.updated_by_agency = actor.agency.value
            row.updated_at = at
            session.flush()
            return _to_action(row)

    def add(
        self,
        district_id: str,
        assignment: IncidentActionAssignment,
        actor: AuthenticatedUser,
        assigned_on: date,
    ) -> IncidentAction:
        action_id = f"{district_id}-assigned-{next(self._sequence)}"
        with self._sessions.begin() as session:
            while session.get(IncidentActionRow, action_id) is not None:
                action_id = f"{district_id}-assigned-{next(self._sequence)}"
            row = IncidentActionRow(
                action_id=action_id,
                district_id=district_id,
                agency=assignment.agency.value,
                origin=ActionOrigin.ASSIGNED.value,
                source_condition=None,
                is_lead=False,
                description=assignment.description,
                status=ActionStatus.NOT_STARTED.value,
                due_on=assignment.due_on,
                assigned_by=actor.display_name,
                assigned_by_role=f"{actor.job_title}, {actor.agency_short_name}",
                assigned_on=assigned_on,
                location_name=assignment.location_name,
                latitude=assignment.latitude,
                longitude=assignment.longitude,
            )
            session.add(row)
            session.flush()
            return _to_action(row)

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
        with self._sessions.begin() as session:
            existing = session.get(IncidentActionRow, action_id)
            if existing is not None:
                return _to_action(existing)
            row = IncidentActionRow(
                action_id=action_id,
                district_id=district_id,
                agency=agency.value,
                origin=ActionOrigin.PLAYBOOK.value,
                source_condition=source_condition,
                is_lead=is_lead,
                description=description,
                status=ActionStatus.NOT_STARTED.value,
                due_on=due_on,
                assigned_by="ClimaHealth playbook",
                assigned_by_role="Standing agency mandate",
                assigned_on=assigned_on,
            )
            session.add(row)
            session.flush()
            return _to_action(row)


class PostgresActionTransitionStore:
    """Append-only: only INSERT is ever issued against action_transitions."""

    def __init__(self, sessions: SessionFactory) -> None:
        self._sessions = sessions

    def record(self, transition: ActionTransition) -> None:
        with self._sessions.begin() as session:
            session.add(
                ActionTransitionRow(
                    action_id=transition.action_id,
                    district_id=transition.district_id,
                    from_status=(transition.from_status.value if transition.from_status else None),
                    to_status=transition.to_status.value,
                    actor_name=transition.actor_name,
                    actor_agency=transition.actor_agency.value,
                    actor_role=transition.actor_role,
                    occurred_at=transition.occurred_at,
                )
            )

    def _read(self, rows: list[ActionTransitionRow]) -> tuple[ActionTransition, ...]:
        return tuple(
            ActionTransition(
                action_id=row.action_id,
                district_id=row.district_id,
                from_status=ActionStatus(row.from_status) if row.from_status else None,
                to_status=ActionStatus(row.to_status),
                actor_name=row.actor_name,
                actor_agency=Agency(row.actor_agency),
                actor_role=row.actor_role,
                occurred_at=row.occurred_at,
            )
            for row in rows
        )

    def for_action(self, action_id: str) -> tuple[ActionTransition, ...]:
        with self._sessions.begin() as session:
            rows = session.scalars(
                select(ActionTransitionRow)
                .where(ActionTransitionRow.action_id == action_id)
                .order_by(ActionTransitionRow.id)
            ).all()
            return self._read(list(rows))

    def for_district(self, district_id: str) -> tuple[ActionTransition, ...]:
        with self._sessions.begin() as session:
            rows = session.scalars(
                select(ActionTransitionRow)
                .where(ActionTransitionRow.district_id == district_id)
                .order_by(ActionTransitionRow.id)
            ).all()
            return self._read(list(rows))
