from climahealth.services.access import AuthenticatedUser
from climahealth.services.gamification_service import GamificationService
from climahealth.services.ports import CitizenStore, PayoutSender
from climahealth.services.rewards import (
    MobileMoneyNetwork,
    Redemption,
    RedemptionRefused,
    network_for_number,
    quote_for,
)


class RewardsService:
    """Turning points into mobile money.

    Two rules the whole service exists to hold: a Guardian under 18 is never paid, and
    points are only spent if the transfer actually succeeded.
    """

    def __init__(
        self,
        gamification: GamificationService,
        citizens: CitizenStore,
        payouts: PayoutSender,
    ) -> None:
        self._gamification = gamification
        self._citizens = citizens
        self._payouts = payouts

    def redeem(
        self,
        user: AuthenticatedUser,
        user_id: str,
        mobile_money_number: str,
        network: MobileMoneyNetwork | None = None,
    ) -> Redemption:
        guardian = self._gamification.resolve(user, user_id)
        citizen = self._citizens.find(guardian.user_id)
        if citizen is None:
            raise RedemptionRefused("This account is not a registered Guardian")

        quote = quote_for(guardian.points, citizen.age_band)
        if not quote.can_redeem:
            raise RedemptionRefused(quote.reason or "This reward cannot be taken yet")

        resolved = network or network_for_number(mobile_money_number)
        if resolved is None:
            raise RedemptionRefused("That number does not look like a Ghanaian mobile money number")

        redemption = self._payouts.pay(
            user_id=guardian.user_id,
            recipient=mobile_money_number,
            network=resolved,
            cedis=quote.cedis,
            points_spent=quote.redeemable_points,
        )

        if redemption.points_spent > 0:
            self._gamification.spend(guardian.user_id, redemption.points_spent)

        return redemption
