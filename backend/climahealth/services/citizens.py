from enum import StrEnum

from pydantic import Field

from climahealth.services.models import ServiceModel
from climahealth.services.narration import NarrationLanguage

MINIMUM_AGE_STATED = 6


class AgeBand(StrEnum):
    """The age a Guardian tells us, in bands rather than a date of birth.

    We ask for a band because a band is all the platform actually needs, and asking a
    child for their birthday to run a public-health app is more than we can justify
    holding. It is not a demographic field: it decides which content a person sees, which
    missions they may be given, and which rewards they may be offered.
    """

    CHILD = "6_12"
    TEEN = "13_17"
    YOUNG_ADULT = "18_34"
    ADULT = "35_59"
    ELDER = "60_plus"


class GuardianTier(StrEnum):
    """The experience a Guardian gets, per proposal section 11.4."""

    ANANSI = "anansi"
    RISK_SCOUT = "risk_scout"
    COMMUNITY_CHAMPION = "community_champion"
    VOICE_FIRST = "voice_first"


AGE_BAND_LABELS: dict[AgeBand, str] = {
    AgeBand.CHILD: "6 to 12",
    AgeBand.TEEN: "13 to 17",
    AgeBand.YOUNG_ADULT: "18 to 34",
    AgeBand.ADULT: "35 to 59",
    AgeBand.ELDER: "60 and above",
}

TIER_FOR_AGE_BAND: dict[AgeBand, GuardianTier] = {
    AgeBand.CHILD: GuardianTier.ANANSI,
    AgeBand.TEEN: GuardianTier.RISK_SCOUT,
    AgeBand.YOUNG_ADULT: GuardianTier.COMMUNITY_CHAMPION,
    AgeBand.ADULT: GuardianTier.COMMUNITY_CHAMPION,
    # Voice-first is the default for elders because proposal section 11.4 makes it a full
    # tier with equal earning power, not a fallback. It can be changed in settings.
    AgeBand.ELDER: GuardianTier.VOICE_FIRST,
}

TIER_NAMES: dict[GuardianTier, str] = {
    GuardianTier.ANANSI: "Anansi's Climate Tales",
    GuardianTier.RISK_SCOUT: "Risk Scout",
    GuardianTier.COMMUNITY_CHAMPION: "Community Champion",
    GuardianTier.VOICE_FIRST: "Voice-First Guardian",
}

MINOR_BANDS: frozenset[AgeBand] = frozenset({AgeBand.CHILD, AgeBand.TEEN})


def tier_for(age_band: AgeBand) -> GuardianTier:
    return TIER_FOR_AGE_BAND[age_band]


def is_minor(age_band: AgeBand) -> bool:
    return age_band in MINOR_BANDS


def may_be_offered_health_insurance(age_band: AgeBand) -> bool:
    """Proposal section 12.3: under-18s are already exempt from premiums.

    Offering a minor free insurance would mean nothing, and offering health rewards to
    a child in exchange for fieldwork would be wrong. Their rewards are class-level and
    their missions stay supervised.
    """
    return not is_minor(age_band)


def missions_must_be_supervised(age_band: AgeBand) -> bool:
    return is_minor(age_band)


class CitizenRegistration(ServiceModel):
    """What we ask a citizen for, and nothing else.

    No password and no verification code. A one-time code costs money to send and turns
    the first thirty seconds of a public-health app into a chore, which is exactly the
    friction that stops the people most at risk from ever arriving. The account holds no
    money and grants no access to anybody else's data, so the cost of a wrong name is
    close to nothing.
    """

    display_name: str = Field(min_length=1, max_length=60)
    district_id: str
    age_band: AgeBand
    language: NarrationLanguage = NarrationLanguage.ENGLISH
    # Optional, and only so the warning can reach a phone that cannot open the app.
    phone_number: str | None = Field(default=None, max_length=20)


class CitizenIdentity(ServiceModel):
    user_id: str
    display_name: str
    district_id: str
    age_band: AgeBand
    age_band_label: str
    tier: GuardianTier
    tier_name: str
    language: NarrationLanguage
    is_minor: bool
    supervised_missions_only: bool
    health_rewards_available: bool


def identity_for(user_id: str, registration: CitizenRegistration) -> CitizenIdentity:
    tier = tier_for(registration.age_band)
    return CitizenIdentity(
        user_id=user_id,
        display_name=registration.display_name.strip(),
        district_id=registration.district_id,
        age_band=registration.age_band,
        age_band_label=AGE_BAND_LABELS[registration.age_band],
        tier=tier,
        tier_name=TIER_NAMES[tier],
        language=registration.language,
        is_minor=is_minor(registration.age_band),
        supervised_missions_only=missions_must_be_supervised(registration.age_band),
        health_rewards_available=may_be_offered_health_insurance(registration.age_band),
    )
