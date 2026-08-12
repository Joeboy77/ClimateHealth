from climahealth.services.citizens import CitizenCredentials, CitizenIdentity


class InMemoryCitizenStore:
    """Registered Guardians.

    Phone numbers and password hashes are held apart from the identity so that nothing
    which renders a Guardian profile can accidentally carry either into a response.
    """

    def __init__(self) -> None:
        self._citizens: dict[str, CitizenIdentity] = {}
        self._phone_numbers: dict[str, str] = {}
        self._credentials: dict[str, CitizenCredentials] = {}
        self._by_phone: dict[str, str] = {}

    def add(
        self,
        identity: CitizenIdentity,
        phone_number: str,
        credentials: CitizenCredentials,
    ) -> None:
        self._citizens[identity.user_id] = identity
        self._phone_numbers[identity.user_id] = phone_number
        self._credentials[identity.user_id] = credentials
        self._by_phone[phone_number] = identity.user_id

    def find(self, user_id: str) -> CitizenIdentity | None:
        return self._citizens.get(user_id)

    def find_by_phone(self, phone_number: str) -> CitizenIdentity | None:
        user_id = self._by_phone.get(phone_number)
        return None if user_id is None else self._citizens.get(user_id)

    def phone_number_for(self, user_id: str) -> str | None:
        return self._phone_numbers.get(user_id)

    def credentials_for(self, user_id: str) -> CitizenCredentials | None:
        return self._credentials.get(user_id)

    def phone_number_taken(self, phone_number: str) -> bool:
        return phone_number in self._by_phone

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
