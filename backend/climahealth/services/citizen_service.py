from uuid import uuid4

from climahealth.services.access import (
    Agency,
    AuthenticatedUser,
    UserRole,
    district_scope,
)
from climahealth.services.citizens import (
    CitizenIdentity,
    CitizenRegistration,
    identity_for,
)
from climahealth.services.models import ServiceModel
from climahealth.services.ports import (
    CitizenStore,
    DistrictRepository,
    GuardianStore,
    TokenIssuer,
)

CITIZEN_JOB_TITLE = "Climate Guardian"


class UnknownDistrict(LookupError):
    pass


class CitizenSession(ServiceModel):
    access_token: str
    citizen: CitizenIdentity


class CitizenService:
    """Registration for the public.

    A citizen is scoped to their own district, holds the responder role, and can only
    ever read what the public overview already exposes plus their own Guardian record.
    That is why registration can be this light: the account is not a key to anything
    somebody else would want.
    """

    def __init__(
        self,
        citizens: CitizenStore,
        districts: DistrictRepository,
        tokens: TokenIssuer,
        guardians: GuardianStore,
    ) -> None:
        self._citizens = citizens
        self._districts = districts
        self._tokens = tokens
        self._guardians = guardians

    def register(self, registration: CitizenRegistration) -> CitizenSession:
        if self._districts.find(registration.district_id) is None:
            raise UnknownDistrict(f"Unknown district '{registration.district_id}'")

        identity = identity_for(f"citizen-{uuid4().hex[:12]}", registration)
        self._citizens.add(identity, registration.phone_number)
        # Joining is becoming a Guardian. One step, not two.
        self._guardians.enrol(identity.user_id, identity.display_name, identity.district_id)

        return CitizenSession(
            access_token=self._tokens.issue(self._as_user(identity)),
            citizen=identity,
        )

    def find(self, user_id: str) -> CitizenIdentity | None:
        return self._citizens.find(user_id)

    def _as_user(self, identity: CitizenIdentity) -> AuthenticatedUser:
        return AuthenticatedUser(
            user_id=identity.user_id,
            username=identity.user_id,
            display_name=identity.display_name,
            job_title=CITIZEN_JOB_TITLE,
            agency=Agency.GHANA_HEALTH_SERVICE,
            role=UserRole.RESPONDER,
            scope=district_scope(identity.district_id),
        )
