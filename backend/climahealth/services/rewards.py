from datetime import date
from enum import StrEnum

from pydantic import Field

from climahealth.services.citizens import AgeBand, is_minor
from climahealth.services.models import ServiceModel

# One year of adult NHIS cover. Derived, not chosen: the adult premium runs about
# GHS 35, and the platform values a point at one pesewa, so a year costs 3,500.
# A reward nobody can calculate is a reward nobody trusts.
POINTS_PER_NHIS_YEAR = 3_500
POINTS_PER_CEDI = 100

# Roughly what a Guardian earns from one daily run, used only to tell somebody how
# many days of use still stand between them and cover.
POINTS_PER_DAILY_RUN = 100


class NhisStatus(StrEnum):
    """Where a renewal has got to.

    Requested is not renewed. The platform cannot issue NHIS cover itself; it tells
    Ghana Health Service who has earned it, and an officer does the renewal. Saying
    "renewed" before that happened would be the platform lying on behalf of a
    government scheme.
    """

    REQUESTED = "requested"
    CONFIRMED = "confirmed"


class RenewalQuote(ServiceModel):
    """What a Guardian's points are worth in NHIS cover, and whether they can claim."""

    points: int = Field(ge=0)
    points_required: int
    points_remaining: int = Field(ge=0)
    percent_of_a_year: int = Field(ge=0, le=100)
    approximate_days_of_use_remaining: int = Field(ge=0)
    can_redeem: bool
    reason: str | None = None


class NhisRenewal(ServiceModel):
    reference: str
    user_id: str
    display_name: str
    district_id: str
    points_spent: int = Field(ge=0)
    months_of_cover: int
    status: NhisStatus
    requested_on: date


class RedemptionRefused(RuntimeError):
    pass


def percent_of_a_year(points: int) -> int:
    return min(100, round(points / POINTS_PER_NHIS_YEAR * 100))


def quote_for(points: int, age_band: AgeBand) -> RenewalQuote:
    """What this person can claim today.

    Under-18s are already exempt from NHIS premiums, so there is nothing here for
    them to buy. Their points still build the district shield, and saying so plainly
    is better than showing a child a reward that would mean nothing to them.
    """
    remaining = max(0, POINTS_PER_NHIS_YEAR - points)
    common = {
        "points": points,
        "points_required": POINTS_PER_NHIS_YEAR,
        "points_remaining": remaining,
        "percent_of_a_year": percent_of_a_year(points),
        "approximate_days_of_use_remaining": -(-remaining // POINTS_PER_DAILY_RUN),
    }

    if is_minor(age_band):
        return RenewalQuote(
            **common,
            can_redeem=False,
            reason=(
                "Under-18s are already exempt from NHIS premiums, so your points earn "
                "recognition and school rewards instead. They still build your "
                "district's shield."
            ),
        )

    if points < POINTS_PER_NHIS_YEAR:
        return RenewalQuote(
            **common,
            can_redeem=False,
            reason=f"{remaining} more points until a year of NHIS cover.",
        )

    return RenewalQuote(**common, can_redeem=True)
