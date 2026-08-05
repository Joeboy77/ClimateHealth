from climahealth.services.access import (
    AuthenticatedUser,
    Credentials,
    DistrictAccessDenied,
    InvalidCredentials,
    as_authenticated,
)
from climahealth.services.models import District
from climahealth.services.ports import (
    DistrictNotFound,
    DistrictRepository,
    PasswordHasher,
    TokenIssuer,
    UserRepository,
)


class AccessService:
    def __init__(
        self,
        users: UserRepository,
        tokens: TokenIssuer,
        hasher: PasswordHasher,
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._hasher = hasher

    def login(self, credentials: Credentials) -> tuple[str, AuthenticatedUser]:
        user = self._users.find_by_username(credentials.username)
        if user is None:
            raise InvalidCredentials("Unknown username or password")
        if not self._hasher.verify(credentials.password, user.password_salt, user.password_hash):
            raise InvalidCredentials("Unknown username or password")
        return self._tokens.issue(as_authenticated(user)), as_authenticated(user)

    def identify(self, token: str) -> AuthenticatedUser:
        return self._tokens.decode(token)


class ScopeGuard:
    def __init__(self, districts: DistrictRepository) -> None:
        self._districts = districts

    def resolve_district(self, user: AuthenticatedUser, district_id: str) -> District:
        district = self._districts.find(district_id)
        if district is None:
            raise DistrictNotFound(f"Unknown district '{district_id}'")
        if not user.scope.permits(district_id):
            raise DistrictAccessDenied(district_id)
        return district

    def visible_districts(self, user: AuthenticatedUser) -> tuple[District, ...]:
        return tuple(
            district
            for district in self._districts.all_districts()
            if user.scope.permits(district.district_id)
        )
