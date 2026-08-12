from climahealth.infrastructure.security.passwords import Pbkdf2PasswordHasher
from climahealth.services.access import (
    Agency,
    User,
    UserRole,
    district_scope,
    national_scope,
)

NATIONAL_USERNAME = "national.officer"
NATIONAL_PASSWORD = "national-demo-2026"
MADINA_USERNAME = "madina.officer"
MADINA_PASSWORD = "madina-demo-2026"
EPA_USERNAME = "epa.officer"
EPA_PASSWORD = "epa-demo-2026"
NADMO_USERNAME = "nadmo.officer"
NADMO_PASSWORD = "nadmo-demo-2026"
FIELD_USERNAME = "ohwefo.madina"
FIELD_PASSWORD = "ohwefo-demo-2026"

DEMO_ACCOUNTS: tuple[tuple[str, str], ...] = (
    (NATIONAL_USERNAME, NATIONAL_PASSWORD),
    (MADINA_USERNAME, MADINA_PASSWORD),
    (EPA_USERNAME, EPA_PASSWORD),
    (NADMO_USERNAME, NADMO_PASSWORD),
    (FIELD_USERNAME, FIELD_PASSWORD),
)

_SALTS = {
    NATIONAL_USERNAME: "9f2c1a7b4e6d8f0a3c5b7d9e1f2a4c6b",
    MADINA_USERNAME: "1a3c5e7f9b2d4f6a8c0e2b4d6f8a0c2e",
    EPA_USERNAME: "3b5d7f9a1c3e5b7d9f1a3c5e7b9d1f3a",
    NADMO_USERNAME: "5c7e9b1d3f5a7c9e1b3d5f7a9c1e3b5d",
    FIELD_USERNAME: "7d9f1b3d5a7c9e1f3b5d7f9a1c3e5b7d",
}


def seeded_users(hasher: Pbkdf2PasswordHasher | None = None) -> tuple[User, ...]:
    password_hasher = hasher or Pbkdf2PasswordHasher()

    def build(
        user_id: str,
        username: str,
        password: str,
        display_name: str,
        job_title: str,
        agency: Agency,
        role: UserRole,
        scope_district: str | None,
    ) -> User:
        return User(
            user_id=user_id,
            username=username,
            display_name=display_name,
            job_title=job_title,
            agency=agency,
            role=role,
            scope=(district_scope(scope_district) if scope_district else national_scope()),
            password_salt=_SALTS[username],
            password_hash=password_hasher.hash(password, _SALTS[username]),
        )

    return (
        build(
            "user-national",
            NATIONAL_USERNAME,
            NATIONAL_PASSWORD,
            "Akosua Mensah",
            "National Surveillance Officer",
            Agency.GHANA_HEALTH_SERVICE,
            UserRole.COORDINATOR,
            None,
        ),
        build(
            "user-madina",
            MADINA_USERNAME,
            MADINA_PASSWORD,
            "Kwame Boateng",
            "District Health Officer",
            Agency.GHANA_HEALTH_SERVICE,
            UserRole.COORDINATOR,
            "madina",
        ),
        build(
            "user-epa",
            EPA_USERNAME,
            EPA_PASSWORD,
            "Yaa Ofori",
            "Air Quality Officer",
            Agency.ENVIRONMENTAL_PROTECTION_AGENCY,
            UserRole.RESPONDER,
            None,
        ),
        build(
            "user-nadmo",
            NADMO_USERNAME,
            NADMO_PASSWORD,
            "Ibrahim Alhassan",
            "Flood Response Coordinator",
            Agency.NADMO,
            UserRole.RESPONDER,
            "madina",
        ),
        build(
            "user-ohwefo-madina",
            FIELD_USERNAME,
            FIELD_PASSWORD,
            "Afua Nyarko",
            "Ɔhwɛfoɔ, on-ground officer",
            Agency.DISTRICT_ASSEMBLY,
            UserRole.FIELD_OFFICER,
            "madina",
        ),
    )


class InMemoryUserRepository:
    def __init__(self, users: tuple[User, ...]) -> None:
        self._by_username = {user.username: user for user in users}
        self._by_id = {user.user_id: user for user in users}

    def find_by_username(self, username: str) -> User | None:
        return self._by_username.get(username)

    def find_by_id(self, user_id: str) -> User | None:
        return self._by_id.get(user_id)
