from fastapi import APIRouter

from climahealth.api.dependencies import ContainerDependency, CurrentUser, PermittedDistrict
from climahealth.services.incident_service import IncidentAction
from climahealth.services.prevention import (
    DistrictPreventionRecord,
    PreventionLeaderboard,
    build_leaderboard,
    build_record,
)

router = APIRouter(tags=["prevention"])


@router.get("/prevention", response_model=PreventionLeaderboard)
def get_prevention_leaderboard(
    user: CurrentUser, container: ContainerDependency
) -> PreventionLeaderboard:
    """District distinctions: how reliably each district closed its mandated actions.

    Derived from the append-only action log, so the standing is evidence rather
    than a score somebody typed in.
    """
    districts = container.scope_guard.visible_districts(user)
    grouped: dict[str, list[IncidentAction]] = {}
    for action in container.incident_service.national_actions(districts):
        grouped.setdefault(action.district_id, []).append(action)
    return build_leaderboard(
        districts,
        {district_id: tuple(actions) for district_id, actions in grouped.items()},
        container.clock.today(),
    )


@router.get("/prevention/{district_id}", response_model=DistrictPreventionRecord)
def get_district_prevention_record(
    district: PermittedDistrict, container: ContainerDependency
) -> DistrictPreventionRecord:
    """One district's prevention record and averted hazards."""
    room = container.incident_service.incident_room(district)
    return build_record(district, room.actions, container.clock.today())
