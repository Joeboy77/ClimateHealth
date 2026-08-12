from pydantic import BaseModel, Field

from climahealth.api.schemas.common import ApiModel
from climahealth.services.access import Agency, AuthenticatedUser, ScopeLevel, UserRole


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class ScopeResponse(ApiModel):
    level: ScopeLevel
    district_id: str | None


class AgencyResponse(ApiModel):
    code: Agency
    name: str
    short_name: str


class UserResponse(ApiModel):
    user_id: str
    username: str
    display_name: str
    job_title: str
    agency: AgencyResponse
    role: UserRole
    role_name: str
    can_assign_actions: bool
    can_validate_reports: bool
    scope: ScopeResponse

    @classmethod
    def of(cls, user: AuthenticatedUser) -> "UserResponse":
        return cls(
            user_id=user.user_id,
            username=user.username,
            display_name=user.display_name,
            job_title=user.job_title,
            agency=AgencyResponse(
                code=user.agency,
                name=user.agency_name,
                short_name=user.agency_short_name,
            ),
            role=user.role,
            role_name=user.role_name,
            can_assign_actions=user.coordinates_response,
            can_validate_reports=user.validates_in_the_field,
            scope=ScopeResponse(level=user.scope.level, district_id=user.scope.district_id),
        )


class LoginResponse(ApiModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
