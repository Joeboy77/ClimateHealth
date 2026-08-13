from uuid import uuid4

from climahealth.services.access import AuthenticatedUser
from climahealth.services.gamification_service import GamificationService
from climahealth.services.ports import CitizenStore, Clock, NhisRenewalStore
from climahealth.services.rewards import (
    POINTS_PER_NHIS_YEAR,
    NhisRenewal,
    NhisStatus,
    RedemptionRefused,
    quote_for,
)

MONTHS_OF_COVER = 12


class RewardsService:
    """Turning points into NHIS cover.

    No money moves. The platform cannot renew NHIS itself, so a claim records that a
    Guardian has earned a year and hands that to Ghana Health Service, who do the
    renewal and confirm it. Calling a request a renewal would be the platform lying on
    behalf of a government scheme.

    Two rules the service exists to hold: an under-18 never claims, because they are
    already exempt from premiums, and points are only spent once the claim is recorded.
    """

    def __init__(
        self,
        gamification: GamificationService,
        citizens: CitizenStore,
        renewals: NhisRenewalStore,
        clock: Clock,
    ) -> None:
        self._gamification = gamification
        self._citizens = citizens
        self._renewals = renewals
        self._clock = clock

    def redeem(self, user: AuthenticatedUser, user_id: str) -> NhisRenewal:
        guardian = self._gamification.resolve(user, user_id)
        citizen = self._citizens.find(guardian.user_id)
        if citizen is None:
            raise RedemptionRefused("This account is not a registered Guardian")

        quote = quote_for(guardian.points, citizen.age_band)
        if not quote.can_redeem:
            raise RedemptionRefused(quote.reason or "This reward cannot be claimed yet")

        renewal = NhisRenewal(
            reference=f"NHIS-{uuid4().hex[:10].upper()}",
            user_id=guardian.user_id,
            display_name=guardian.display_name,
            district_id=guardian.district_id,
            points_spent=POINTS_PER_NHIS_YEAR,
            months_of_cover=MONTHS_OF_COVER,
            status=NhisStatus.REQUESTED,
            requested_on=self._clock.today(),
        )
        self._renewals.record(renewal)
        self._gamification.spend(guardian.user_id, POINTS_PER_NHIS_YEAR)
        return renewal

    def claims_for(self, district_id: str | None = None) -> tuple[NhisRenewal, ...]:
        return self._renewals.all_renewals(district_id)

    def confirm(self, reference: str) -> NhisRenewal:
        """Ghana Health Service marks a renewal as actually done."""
        confirmed = self._renewals.confirm(reference)
        if confirmed is None:
            raise RedemptionRefused(f"Unknown renewal '{reference}'")
        return confirmed
