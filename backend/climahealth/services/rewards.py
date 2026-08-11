from decimal import ROUND_DOWN, Decimal
from enum import StrEnum

from pydantic import Field

from climahealth.services.citizens import AgeBand, is_minor
from climahealth.services.models import ServiceModel

# 100 points is one cedi. Deliberately a round number a person can hold in their head:
# a reward nobody can calculate is a reward nobody trusts.
POINTS_PER_CEDI = 100
# Below this the network fee costs more than the reward is worth.
MINIMUM_REDEEMABLE_POINTS = 500
# A ceiling per person per day. Not because we expect fraud, but because an unbounded
# payout path is the one bug you cannot take back.
DAILY_PAYOUT_CEILING_GHS = Decimal("20.00")


class MobileMoneyNetwork(StrEnum):
    """Moolre transfer channels."""

    MTN = "1"
    TELECEL = "6"
    AT = "7"


NETWORK_NAMES: dict[MobileMoneyNetwork, str] = {
    MobileMoneyNetwork.MTN: "MTN",
    MobileMoneyNetwork.TELECEL: "Telecel",
    MobileMoneyNetwork.AT: "AT",
}


class PayoutMode(StrEnum):
    """Whether a redemption actually moves money."""

    PREVIEW = "preview"
    LIVE = "live"


class RedemptionQuote(ServiceModel):
    """What a Guardian's points are worth, and whether they can take it yet."""

    points: int = Field(ge=0)
    redeemable_points: int = Field(ge=0)
    cedis: Decimal
    minimum_points: int
    points_per_cedi: int
    can_redeem: bool
    reason: str | None = None


class Redemption(ServiceModel):
    reference: str
    points_spent: int = Field(ge=0)
    cedis: Decimal
    recipient: str
    network: MobileMoneyNetwork
    network_name: str
    accepted: bool
    mode: PayoutMode
    provider_code: str
    provider_message: str
    transaction_id: str | None = None


class RedemptionRefused(RuntimeError):
    pass


def cedis_for(points: int) -> Decimal:
    """Whole tenths of a cedi, always rounded down. Never pay out more than was earned."""
    value = Decimal(points) / Decimal(POINTS_PER_CEDI)
    return value.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def points_for_cedis(cedis: Decimal) -> int:
    return int(cedis * POINTS_PER_CEDI)


def quote_for(points: int, age_band: AgeBand) -> RedemptionQuote:
    """What this person can take out today.

    Minors cannot be paid. Proposal section 12.3 keeps under-18s out of the money
    pathway entirely: paying a child for fieldwork is a different product with a
    different set of obligations, and not one we are equipped to run.
    """
    cedis = cedis_for(points)

    if is_minor(age_band):
        return RedemptionQuote(
            points=points,
            redeemable_points=0,
            cedis=Decimal("0.00"),
            minimum_points=MINIMUM_REDEEMABLE_POINTS,
            points_per_cedi=POINTS_PER_CEDI,
            can_redeem=False,
            reason=(
                "Guardians under 18 earn recognition and school rewards rather than "
                "money. Your points still build your district's shield."
            ),
        )

    if points < MINIMUM_REDEEMABLE_POINTS:
        needed = MINIMUM_REDEEMABLE_POINTS - points
        return RedemptionQuote(
            points=points,
            redeemable_points=0,
            cedis=cedis,
            minimum_points=MINIMUM_REDEEMABLE_POINTS,
            points_per_cedi=POINTS_PER_CEDI,
            can_redeem=False,
            reason=f"{needed} more points until you can cash out.",
        )

    capped_points = min(points, points_for_cedis(DAILY_PAYOUT_CEILING_GHS))
    return RedemptionQuote(
        points=points,
        redeemable_points=capped_points,
        cedis=cedis_for(capped_points),
        minimum_points=MINIMUM_REDEEMABLE_POINTS,
        points_per_cedi=POINTS_PER_CEDI,
        can_redeem=True,
    )


def network_for_number(number: str) -> MobileMoneyNetwork | None:
    """Ghanaian mobile money prefixes, so nobody has to pick their own network."""
    digits = number.strip().replace(" ", "")
    local = "0" + digits[3:] if digits.startswith("233") else digits
    prefix = local[:3]

    if prefix in {"024", "054", "055", "059", "025", "053"}:
        return MobileMoneyNetwork.MTN
    if prefix in {"020", "050"}:
        return MobileMoneyNetwork.TELECEL
    if prefix in {"027", "057", "026", "056"}:
        return MobileMoneyNetwork.AT
    return None


def as_local_number(number: str) -> str:
    """Moolre wants a number beginning with 0."""
    digits = number.strip().replace(" ", "").replace("+", "")
    if digits.startswith("233"):
        return "0" + digits[3:]
    return digits
