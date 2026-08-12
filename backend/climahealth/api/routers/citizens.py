from fastapi import APIRouter, HTTPException, status

from climahealth.api.dependencies import ContainerDependency, CurrentUser
from climahealth.api.schemas.common import ApiModel
from climahealth.services.citizen_service import (
    CitizenSession,
    PhoneNumberAlreadyRegistered,
    SignInRejected,
    UnknownDistrict,
)
from climahealth.services.citizens import (
    AGE_BAND_LABELS,
    TIER_NAMES,
    AgeBand,
    CitizenIdentity,
    CitizenLogin,
    CitizenRegistration,
    GuardianTier,
    tier_for,
)
from climahealth.services.phone_numbers import InvalidPhoneNumber

router = APIRouter(tags=["citizens"])


class AgeBandOption(ApiModel):
    """Offered to the citizen at sign-up, with what it actually changes."""

    age_band: AgeBand
    label: str
    tier: GuardianTier
    tier_name: str
    supervised_missions_only: bool
    health_rewards_available: bool


@router.get("/citizens/age-bands", response_model=list[AgeBandOption])
def list_age_bands() -> list[AgeBandOption]:
    """The age bands, open so the sign-up screen can render before anybody has an account."""
    from climahealth.services.citizens import (
        may_be_offered_health_insurance,
        missions_must_be_supervised,
    )

    return [
        AgeBandOption(
            age_band=band,
            label=AGE_BAND_LABELS[band],
            tier=tier_for(band),
            tier_name=TIER_NAMES[tier_for(band)],
            supervised_missions_only=missions_must_be_supervised(band),
            health_rewards_available=may_be_offered_health_insurance(band),
        )
        for band in AgeBand
    ]


@router.post(
    "/citizens",
    response_model=CitizenSession,
    status_code=status.HTTP_201_CREATED,
)
def register_citizen(
    registration: CitizenRegistration, container: ContainerDependency
) -> CitizenSession:
    """Register a Guardian with a phone number and a password.

    Still no one-time code. A verification SMS costs money to send and turns the first
    thirty seconds of a public-health app into a chore, which is the friction that stops
    the people most at risk from ever arriving. The number is required because the
    warning has to reach a phone that cannot open the app.
    """
    try:
        return container.citizen_service.register(registration)
    except UnknownDistrict as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except InvalidPhoneNumber as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    except PhoneNumberAlreadyRegistered as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/citizens/login", response_model=CitizenSession)
def sign_in_citizen(login: CitizenLogin, container: ContainerDependency) -> CitizenSession:
    """Sign back in with the phone number and password used at registration."""
    try:
        return container.citizen_service.sign_in(login)
    except SignInRejected as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error


@router.get("/citizens/me", response_model=CitizenIdentity)
def get_citizen(user: CurrentUser, container: ContainerDependency) -> CitizenIdentity:
    """The signed-in Guardian's own record."""
    citizen = container.citizen_service.find(user.user_id)
    if citizen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This account is not a registered Guardian",
        )
    return citizen
