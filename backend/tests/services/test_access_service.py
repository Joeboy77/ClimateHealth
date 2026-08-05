from datetime import timedelta

import pytest

from climahealth.infrastructure.security.passwords import Pbkdf2PasswordHasher, generate_salt
from climahealth.infrastructure.security.tokens import JwtTokenIssuer, WeakTokenSecret
from climahealth.infrastructure.seed.districts import InMemoryDistrictRepository
from climahealth.infrastructure.seed.users import (
    MADINA_PASSWORD,
    MADINA_USERNAME,
    NATIONAL_PASSWORD,
    NATIONAL_USERNAME,
    InMemoryUserRepository,
    seeded_users,
)
from climahealth.services.access import (
    Credentials,
    DistrictAccessDenied,
    InvalidCredentials,
    InvalidToken,
    ScopeLevel,
    district_scope,
    national_scope,
)
from climahealth.services.access_service import AccessService, ScopeGuard
from climahealth.services.ports import DistrictNotFound

TEST_SECRET = "test-secret-not-for-production-0123456789"
FAST_HASHER = Pbkdf2PasswordHasher(iterations=1)


@pytest.fixture
def access_service() -> AccessService:
    return AccessService(
        users=InMemoryUserRepository(seeded_users(FAST_HASHER)),
        tokens=JwtTokenIssuer(TEST_SECRET),
        hasher=FAST_HASHER,
    )


@pytest.fixture
def scope_guard() -> ScopeGuard:
    return ScopeGuard(InMemoryDistrictRepository())


def test_national_scope_permits_every_district():
    scope = national_scope()

    assert scope.permits("madina") is True
    assert scope.permits("wa") is True


def test_district_scope_permits_only_its_own_district():
    scope = district_scope("madina")

    assert scope.permits("madina") is True
    assert scope.permits("wa") is False


def test_login_returns_a_token_and_the_national_scope(access_service):
    token, user = access_service.login(
        Credentials(username=NATIONAL_USERNAME, password=NATIONAL_PASSWORD)
    )

    assert token
    assert user.scope.level is ScopeLevel.NATIONAL
    assert user.scope.district_id is None


def test_login_returns_the_district_scope_for_a_district_officer(access_service):
    _, user = access_service.login(Credentials(username=MADINA_USERNAME, password=MADINA_PASSWORD))

    assert user.scope.level is ScopeLevel.DISTRICT
    assert user.scope.district_id == "madina"


def test_login_with_a_wrong_password_is_refused(access_service):
    with pytest.raises(InvalidCredentials):
        access_service.login(Credentials(username=NATIONAL_USERNAME, password="wrong"))


def test_login_with_an_unknown_username_is_refused(access_service):
    with pytest.raises(InvalidCredentials):
        access_service.login(Credentials(username="nobody", password=NATIONAL_PASSWORD))


def test_a_token_round_trips_to_the_same_identity_and_scope(access_service):
    token, user = access_service.login(
        Credentials(username=MADINA_USERNAME, password=MADINA_PASSWORD)
    )

    assert access_service.identify(token) == user


def test_a_token_signed_with_another_secret_is_rejected(access_service):
    forged = JwtTokenIssuer("attacker-secret-0123456789abcdefghij").issue(
        access_service.login(Credentials(username=MADINA_USERNAME, password=MADINA_PASSWORD))[1]
    )

    with pytest.raises(InvalidToken):
        access_service.identify(forged)


def test_a_malformed_token_is_rejected(access_service):
    with pytest.raises(InvalidToken):
        access_service.identify("not-a-jwt")


def test_an_expired_token_is_rejected():
    issuer = JwtTokenIssuer(TEST_SECRET, lifetime=timedelta(seconds=-1))
    service = AccessService(
        users=InMemoryUserRepository(seeded_users(FAST_HASHER)),
        tokens=issuer,
        hasher=FAST_HASHER,
    )
    token, _ = service.login(Credentials(username=NATIONAL_USERNAME, password=NATIONAL_PASSWORD))

    with pytest.raises(InvalidToken):
        service.identify(token)


def test_a_district_user_cannot_escalate_by_editing_the_scope_claim(access_service):
    _, madina_user = access_service.login(
        Credentials(username=MADINA_USERNAME, password=MADINA_PASSWORD)
    )
    escalated = madina_user.model_copy(update={"scope": national_scope()})
    forged = JwtTokenIssuer("attacker-secret-0123456789abcdefghij").issue(escalated)

    with pytest.raises(InvalidToken):
        access_service.identify(forged)


def test_national_user_resolves_any_district(access_service, scope_guard):
    _, user = access_service.login(
        Credentials(username=NATIONAL_USERNAME, password=NATIONAL_PASSWORD)
    )

    assert scope_guard.resolve_district(user, "wa").district_id == "wa"


def test_district_user_resolves_its_own_district(access_service, scope_guard):
    _, user = access_service.login(Credentials(username=MADINA_USERNAME, password=MADINA_PASSWORD))

    assert scope_guard.resolve_district(user, "madina").district_id == "madina"


def test_district_user_is_refused_another_district(access_service, scope_guard):
    _, user = access_service.login(Credentials(username=MADINA_USERNAME, password=MADINA_PASSWORD))

    with pytest.raises(DistrictAccessDenied):
        scope_guard.resolve_district(user, "wa")


def test_unknown_district_is_reported_as_not_found(access_service, scope_guard):
    _, user = access_service.login(
        Credentials(username=NATIONAL_USERNAME, password=NATIONAL_PASSWORD)
    )

    with pytest.raises(DistrictNotFound):
        scope_guard.resolve_district(user, "atlantis")


def test_national_user_sees_every_district(access_service, scope_guard):
    _, user = access_service.login(
        Credentials(username=NATIONAL_USERNAME, password=NATIONAL_PASSWORD)
    )

    assert len(scope_guard.visible_districts(user)) >= 5


def test_district_user_sees_only_its_own_district(access_service, scope_guard):
    _, user = access_service.login(Credentials(username=MADINA_USERNAME, password=MADINA_PASSWORD))

    visible = scope_guard.visible_districts(user)

    assert [district.district_id for district in visible] == ["madina"]


def test_password_hashing_is_salted_and_verifiable():
    hasher = Pbkdf2PasswordHasher(iterations=1)
    salt = generate_salt()
    other_salt = generate_salt()

    assert hasher.verify("secret", salt, hasher.hash("secret", salt)) is True
    assert hasher.verify("wrong", salt, hasher.hash("secret", salt)) is False
    assert hasher.hash("secret", salt) != hasher.hash("secret", other_salt)


def test_a_short_token_secret_is_refused_outright():
    with pytest.raises(WeakTokenSecret):
        JwtTokenIssuer("too-short")


def test_seeded_passwords_are_never_stored_in_plain_text():
    for user in seeded_users(FAST_HASHER):
        assert NATIONAL_PASSWORD not in user.password_hash
        assert MADINA_PASSWORD not in user.password_hash
        assert len(user.password_hash) == 64
