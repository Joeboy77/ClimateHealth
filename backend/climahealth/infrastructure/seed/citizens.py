from climahealth.services.citizens import CitizenIdentity


class InMemoryCitizenStore:
    """Registered Guardians.

    Phone numbers are held apart from the identity so that nothing which renders a
    Guardian profile can accidentally carry a phone number into a response.
    """

    def __init__(self) -> None:
        self._citizens: dict[str, CitizenIdentity] = {}
        self._phone_numbers: dict[str, str] = {}

    def add(self, identity: CitizenIdentity, phone_number: str | None) -> None:
        self._citizens[identity.user_id] = identity
        if phone_number:
            self._phone_numbers[identity.user_id] = phone_number

    def find(self, user_id: str) -> CitizenIdentity | None:
        return self._citizens.get(user_id)

    def for_district(self, district_id: str) -> tuple[CitizenIdentity, ...]:
        return tuple(
            citizen for citizen in self._citizens.values() if citizen.district_id == district_id
        )

    def phone_numbers_in(self, district_id: str) -> tuple[str, ...]:
        return tuple(
            self._phone_numbers[citizen.user_id]
            for citizen in self.for_district(district_id)
            if citizen.user_id in self._phone_numbers
        )
