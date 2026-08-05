from enum import StrEnum

from pydantic import Field

from climahealth.services.models import ServiceModel


class Agency(StrEnum):
    GHANA_HEALTH_SERVICE = "ghs"
    ENVIRONMENTAL_PROTECTION_AGENCY = "epa"
    METEOROLOGICAL_AGENCY = "gmet"
    NADMO = "nadmo"
    DISTRICT_ASSEMBLY = "assembly"


AGENCY_NAMES: dict[Agency, str] = {
    Agency.GHANA_HEALTH_SERVICE: "Ghana Health Service",
    Agency.ENVIRONMENTAL_PROTECTION_AGENCY: "Environmental Protection Agency",
    Agency.METEOROLOGICAL_AGENCY: "Ghana Meteorological Agency",
    Agency.NADMO: "National Disaster Management Organisation",
    Agency.DISTRICT_ASSEMBLY: "District Assembly",
}

AGENCY_SHORT_NAMES: dict[Agency, str] = {
    Agency.GHANA_HEALTH_SERVICE: "GHS",
    Agency.ENVIRONMENTAL_PROTECTION_AGENCY: "EPA",
    Agency.METEOROLOGICAL_AGENCY: "GMet",
    Agency.NADMO: "NADMO",
    Agency.DISTRICT_ASSEMBLY: "Assembly",
}


class UserRole(StrEnum):
    """What a user may do with assigned work.

    A coordinator owns the response for their scope: they assign actions to
    agencies and may change any status within that scope. A responder carries out
    work and may only move the actions assigned to their own agency.
    """

    COORDINATOR = "coordinator"
    RESPONDER = "responder"


ROLE_NAMES: dict[UserRole, str] = {
    UserRole.COORDINATOR: "Response coordinator",
    UserRole.RESPONDER: "Agency responder",
}


class ScopeLevel(StrEnum):
    NATIONAL = "national"
    DISTRICT = "district"


class Scope(ServiceModel):
    level: ScopeLevel
    district_id: str | None = None

    def permits(self, district_id: str) -> bool:
        if self.level is ScopeLevel.NATIONAL:
            return True
        return self.district_id == district_id


class User(ServiceModel):
    user_id: str
    username: str
    display_name: str
    job_title: str
    agency: Agency
    role: UserRole
    scope: Scope
    password_salt: str
    password_hash: str


class AuthenticatedUser(ServiceModel):
    user_id: str
    username: str
    display_name: str
    job_title: str
    agency: Agency
    role: UserRole
    scope: Scope

    @property
    def role_name(self) -> str:
        return ROLE_NAMES[self.role]

    @property
    def coordinates_response(self) -> bool:
        return self.role is UserRole.COORDINATOR

    def may_update_action_of(self, assigned_agency: Agency) -> bool:
        """Coordinators may move anything in scope; responders only their own work."""
        return self.coordinates_response or self.agency is assigned_agency

    @property
    def agency_name(self) -> str:
        return AGENCY_NAMES[self.agency]

    @property
    def agency_short_name(self) -> str:
        return AGENCY_SHORT_NAMES[self.agency]


class Credentials(ServiceModel):
    username: str
    password: str = Field(min_length=1)


class InvalidCredentials(RuntimeError):
    pass


class InvalidToken(RuntimeError):
    pass


class ActionNotAssignedToYou(PermissionError):
    def __init__(self, agency_name: str) -> None:
        super().__init__(
            f"This action is assigned to {agency_name}. Only {agency_name} or a response "
            "coordinator can change its status."
        )


class NotACoordinator(PermissionError):
    def __init__(self) -> None:
        super().__init__("Only a response coordinator can assign actions.")


class DistrictAccessDenied(PermissionError):
    def __init__(self, district_id: str) -> None:
        super().__init__(f"Your account is not scoped to district '{district_id}'")
        self.district_id = district_id


def national_scope() -> Scope:
    return Scope(level=ScopeLevel.NATIONAL)


def district_scope(district_id: str) -> Scope:
    return Scope(level=ScopeLevel.DISTRICT, district_id=district_id)


def as_authenticated(user: User) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=user.user_id,
        username=user.username,
        display_name=user.display_name,
        job_title=user.job_title,
        agency=user.agency,
        role=user.role,
        scope=user.scope,
    )
