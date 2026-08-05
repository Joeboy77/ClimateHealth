from fastapi import APIRouter, HTTPException, status

from climahealth.api.dependencies import ContainerDependency, CurrentUser, PermittedDistrict
from climahealth.api.schemas.incident import IncidentActionResponse, IncidentRoomResponse
from climahealth.services.alerts_service import Alert
from climahealth.services.incident_service import (
    IncidentActionAssignment,
    IncidentActionUpdate,
    ReadinessReport,
    UnknownIncidentAction,
)

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[Alert])
def list_alerts(user: CurrentUser, container: ContainerDependency) -> list[Alert]:
    """List active alerts for every district the caller may see."""
    return list(container.alerts_service.active_alerts(user))


@router.get("/alerts/{alert_id}", response_model=Alert)
def get_alert(alert_id: str, user: CurrentUser, container: ContainerDependency) -> Alert:
    """Return one alert with its explainable reasons and recommended action."""
    alert = container.alerts_service.find_alert(user, alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown alert '{alert_id}'"
        )
    return alert


@router.get("/incident", response_model=list[IncidentActionResponse])
def list_incident_actions(
    user: CurrentUser, container: ContainerDependency
) -> list[IncidentActionResponse]:
    """Every action across the districts the caller may see, for the national board."""
    districts = container.scope_guard.visible_districts(user)
    now = container.clock.now()
    return [
        IncidentActionResponse.of(action, now)
        for action in container.incident_service.national_actions(districts)
    ]


@router.get("/incident/{district_id}", response_model=IncidentRoomResponse)
def get_incident_room(
    district: PermittedDistrict, container: ContainerDependency
) -> IncidentRoomResponse:
    """Return the incident room: assigned agency actions and their status."""
    return IncidentRoomResponse.of(
        container.incident_service.incident_room(district), container.clock.now()
    )


@router.post("/incident/{district_id}/action", response_model=IncidentActionResponse)
def update_incident_action(
    district: PermittedDistrict,
    update: IncidentActionUpdate,
    user: CurrentUser,
    container: ContainerDependency,
) -> IncidentActionResponse:
    """Move an action's status. Responders may only move their own agency's work."""
    try:
        return IncidentActionResponse.of(
            container.incident_service.update_action(district, update, user),
            container.clock.now(),
        )
    except UnknownIncidentAction as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post(
    "/incident/{district_id}/assign",
    response_model=IncidentActionResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_incident_action(
    district: PermittedDistrict,
    assignment: IncidentActionAssignment,
    user: CurrentUser,
    container: ContainerDependency,
) -> IncidentActionResponse:
    """Assign a new action to an agency. Coordinators only."""
    return IncidentActionResponse.of(
        container.incident_service.assign_action(district, assignment, user),
        container.clock.now(),
    )


@router.get("/readiness/{district_id}", response_model=ReadinessReport)
def get_readiness(district: PermittedDistrict, container: ContainerDependency) -> ReadinessReport:
    """Return resource readiness: risk versus stock versus community reports."""
    return container.readiness_service.readiness_for(district)
