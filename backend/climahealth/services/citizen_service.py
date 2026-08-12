import secrets
from collections.abc import Callable
from uuid import uuid4

from climahealth.services.access import (
    Agency,
    AuthenticatedUser,
    UserRole,
    district_scope,
)
from climahealth.services.citizens import (
    CitizenCredentials,
    CitizenIdentity,
    CitizenLogin,
    CitizenRegistration,
    identity_for,
)
from climahealth.services.models import ServiceModel
from climahealth.services.phone_numbers import (
    InvalidPhoneNumber,
    validated_local_number,
)
from climahealth.services.ports import (
    CitizenStore,
    DistrictRepository,
    GuardianStore,
    PasswordHasher,
    TokenIssuer,
)

CITIZEN_JOB_TITLE = "Climate Guardian"
SIGN_IN_REJECTED_MESSAGE = "That number and password do not match an account."
SALT_BYTES = 16


def generate_salt() -> str:
    return secrets.token_hex(SALT_BYTES)


class UnknownDistrict(LookupError):
    pass


class PhoneNumberAlreadyRegistered(ValueError):
    pass


class SignInRejected(ValueError):
    """One message for a wrong number and a wrong password alike.

    Saying which half was wrong tells anybody who asks whether a given number has an
    account here, and being a registered Guardian is not something a stranger should be
    able to confirm.
    """


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
        passwords: PasswordHasher,
        make_salt: Callable[[], str] = generate_salt,
    ) -> None:
        self._citizens = citizens
        self._districts = districts
        self._tokens = tokens
        self._guardians = guardians
        self._passwords = passwords
        self._make_salt = make_salt

    def register(self, registration: CitizenRegistration) -> CitizenSession:
        if self._districts.find(registration.district_id) is None:
            raise UnknownDistrict(f"Unknown district '{registration.district_id}'")

        phone_number = validated_local_number(registration.phone_number)
        if self._citizens.phone_number_taken(phone_number):
            raise PhoneNumberAlreadyRegistered(
                "That number already has an account. Sign in instead."
            )

        salt = self._make_salt()
        identity = identity_for(f"citizen-{uuid4().hex[:12]}", registration)
        self._citizens.add(
            identity,
            phone_number,
            CitizenCredentials(
                password_salt=salt,
                password_hash=self._passwords.hash(registration.password, salt),
            ),
        )
        # Joining is becoming a Guardian. One step, not two.
        self._guardians.enrol(identity.user_id, identity.display_name, identity.district_id)

        return CitizenSession(
            access_token=self._tokens.issue(self._as_user(identity)),
            citizen=identity,
        )

    def sign_in(self, login: CitizenLogin) -> CitizenSession:
        try:
            phone_number = validated_local_number(login.phone_number)
        except InvalidPhoneNumber as error:
            raise SignInRejected(SIGN_IN_REJECTED_MESSAGE) from error

        identity = self._citizens.find_by_phone(phone_number)
        credentials = None if identity is None else self._citizens.credentials_for(identity.user_id)
        if identity is None or credentials is None:
            raise SignInRejected(SIGN_IN_REJECTED_MESSAGE)

        if not self._passwords.verify(
            login.password, credentials.password_salt, credentials.password_hash
        ):
            raise SignInRejected(SIGN_IN_REJECTED_MESSAGE)

        # Older accounts predate Guardian enrolment at registration.
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
