from climahealth.services.rewards import NhisRenewal, NhisStatus


class InMemoryNhisRenewalStore:
    """Claims a Guardian has made on their earned NHIS cover.

    Append-mostly: a claim is recorded once and only ever moves from requested to
    confirmed, because the thing being tracked is whether a real renewal happened.
    """

    def __init__(self) -> None:
        self._renewals: list[NhisRenewal] = []

    def record(self, renewal: NhisRenewal) -> None:
        self._renewals.append(renewal)

    def all_renewals(self, district_id: str | None = None) -> tuple[NhisRenewal, ...]:
        return tuple(
            renewal
            for renewal in self._renewals
            if district_id is None or renewal.district_id == district_id
        )

    def confirm(self, reference: str) -> NhisRenewal | None:
        for index, renewal in enumerate(self._renewals):
            if renewal.reference != reference:
                continue
            confirmed = renewal.model_copy(update={"status": NhisStatus.CONFIRMED})
            self._renewals[index] = confirmed
            return confirmed
        return None
