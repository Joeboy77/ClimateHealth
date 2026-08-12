from datetime import date
from pathlib import Path
from tempfile import mkdtemp

import pytest
from fastapi.testclient import TestClient

from climahealth.api.container import Container
from climahealth.api.main import create_app
from climahealth.api.rate_limit import SlidingWindowLimiter
from climahealth.api.settings import Settings
from climahealth.domain.models import ClimateFeatures
from climahealth.infrastructure.ai.template_narrator import TemplateRiskNarrator
from climahealth.infrastructure.climate.context_provider import (
    CalendarContextProvider,
    CommunityReportContextProvider,
    SeasonOverrideContextProvider,
)
from climahealth.infrastructure.climate.providers import DemoOverrideFeatureProvider
from climahealth.infrastructure.clock import FixedClock
from climahealth.infrastructure.events.broadcaster import InMemoryEventBroadcaster
from climahealth.infrastructure.security.passwords import Pbkdf2PasswordHasher
from climahealth.infrastructure.security.tokens import JwtTokenIssuer
from climahealth.infrastructure.seed.citizens import InMemoryCitizenStore
from climahealth.infrastructure.seed.nhis import InMemoryNhisRenewalStore
from climahealth.infrastructure.seed.districts import InMemoryDistrictRepository
from climahealth.infrastructure.seed.gamification import (
    InMemoryGuardianStore,
    InMemoryQuizRepository,
)
from climahealth.infrastructure.seed.incidents import (
    InMemoryActionTransitionStore,
    InMemoryIncidentActionStore,
    InMemoryResourceStockStore,
)
from climahealth.infrastructure.seed.reports import InMemoryReportStore
from climahealth.infrastructure.seed.users import (
    EPA_PASSWORD,
    EPA_USERNAME,
    FIELD_PASSWORD,
    FIELD_USERNAME,
    MADINA_PASSWORD,
    MADINA_USERNAME,
    NADMO_PASSWORD,
    NADMO_USERNAME,
    NATIONAL_PASSWORD,
    NATIONAL_USERNAME,
    InMemoryUserRepository,
    seeded_users,
)
from climahealth.infrastructure.sms.moolre import PreviewSmsSender
from climahealth.infrastructure.sms.sessions import InMemoryUssdSessionStore
from climahealth.infrastructure.storage.photos import LocalPhotoStore
from climahealth.services.access_service import AccessService, ScopeGuard
from climahealth.services.alerts_service import AlertsService
from climahealth.services.citizen_service import CitizenService
from climahealth.services.demo_service import DemoService
from climahealth.services.forecast_service import ForecastService
from climahealth.services.gamification_service import GamificationService
from climahealth.services.incident_service import IncidentService
from climahealth.services.models import District
from climahealth.services.outreach_service import OutreachService
from climahealth.services.readiness_service import ReadinessService
from climahealth.services.reports_service import ReportsService
from climahealth.services.rewards_service import RewardsService
from climahealth.services.risk_service import RiskService
from climahealth.services.tickets import InMemoryTicketStore

TEST_SECRET = "api-test-secret-that-is-long-enough-0123456789"
TEST_DAY = date(2026, 7, 27)
FAST_HASHER = Pbkdf2PasswordHasher(iterations=1)

BASELINE_FEATURES = ClimateFeatures(
    observed_on=TEST_DAY,
    rainfall_7d_mm=12.0,
    rainfall_14d_mm=25.0,
    consecutive_dry_days=2,
    humidity_mean_percent=68.0,
    temperature_mean_c=27.0,
    temperature_max_c=31.0,
    dust_concentration_ug_m3=8.0,
    particulate_matter_10_ug_m3=22.0,
)


class StubFeatureProvider:
    def __init__(self, features: ClimateFeatures = BASELINE_FEATURES) -> None:
        self.features = features
        self.requested: list[str] = []

    def features_for(self, district: District) -> ClimateFeatures:
        self.requested.append(district.district_id)
        return self.features


@pytest.fixture
def stub_provider() -> StubFeatureProvider:
    return StubFeatureProvider()


@pytest.fixture
def override_provider(stub_provider) -> DemoOverrideFeatureProvider:
    return DemoOverrideFeatureProvider(stub_provider)


@pytest.fixture
def context_provider() -> SeasonOverrideContextProvider:
    return SeasonOverrideContextProvider(CalendarContextProvider())


@pytest.fixture
def container(override_provider, context_provider) -> Container:
    clock = FixedClock(TEST_DAY)
    report_store = InMemoryReportStore()
    guardians = InMemoryGuardianStore()
    quizzes = InMemoryQuizRepository()
    citizen_store = InMemoryCitizenStore()
    risk_service = RiskService(
        provider=override_provider,
        context_provider=CommunityReportContextProvider(context_provider, report_store),
        clock=clock,
    )
    gamification_service = GamificationService(
        guardians=guardians,
        quizzes=quizzes,
        reports=report_store,
        risk_service=risk_service,
        clock=clock,
    )
    scope_guard = ScopeGuard(InMemoryDistrictRepository())
    narrator = TemplateRiskNarrator()
    broadcaster = InMemoryEventBroadcaster()
    return Container(
        access_service=AccessService(
            users=InMemoryUserRepository(seeded_users(FAST_HASHER)),
            tokens=JwtTokenIssuer(TEST_SECRET),
            hasher=FAST_HASHER,
        ),
        scope_guard=scope_guard,
        risk_service=risk_service,
        forecast_service=ForecastService(risk_service=risk_service, narrator=narrator),
        demo_service=DemoService(
            overrides=override_provider,
            seasons=context_provider,
            clock=clock,
            events=broadcaster,
        ),
        alerts_service=AlertsService(
            risk_service=risk_service, scope_guard=scope_guard, narrator=narrator
        ),
        incident_service=IncidentService(
            risk_service=risk_service,
            actions=InMemoryIncidentActionStore(),
            transitions=InMemoryActionTransitionStore(),
            clock=clock,
            events=broadcaster,
        ),
        readiness_service=ReadinessService(
            risk_service=risk_service,
            stocks=InMemoryResourceStockStore(),
            reports=report_store,
        ),
        reports_service=ReportsService(
            reports=report_store,
            scope_guard=scope_guard,
            clock=clock,
            events=broadcaster,
        ),
        gamification_service=gamification_service,
        rewards_service=RewardsService(
            gamification=gamification_service,
            citizens=citizen_store,
            renewals=InMemoryNhisRenewalStore(),
            clock=clock,
        ),
        guardians=guardians,
        quizzes=quizzes,
        broadcaster=broadcaster,
        clock=clock,
        district_repository=InMemoryDistrictRepository(),
        settings=Settings(token_secret=TEST_SECRET),
        tickets=InMemoryTicketStore(),
        public_limiter=SlidingWindowLimiter(),
        photo_store=LocalPhotoStore(Path(mkdtemp())),
        citizen_store=citizen_store,
        citizen_service=CitizenService(
            citizens=citizen_store,
            districts=InMemoryDistrictRepository(),
            tokens=JwtTokenIssuer(TEST_SECRET),
            guardians=guardians,
            passwords=FAST_HASHER,
        ),
        outreach_service=OutreachService(
            risk_service=risk_service,
            sms_sender=PreviewSmsSender(),
            sessions=InMemoryUssdSessionStore(),
        ),
    )


@pytest.fixture
def client(container) -> TestClient:
    return TestClient(
        create_app(
            container=container,
            settings=Settings(token_secret=TEST_SECRET),
        )
    )


def token_for(client: TestClient, username: str, password: str) -> str:
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def national_headers(client) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_for(client, NATIONAL_USERNAME, NATIONAL_PASSWORD)}"}


@pytest.fixture
def madina_headers(client) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_for(client, MADINA_USERNAME, MADINA_PASSWORD)}"}


@pytest.fixture
def epa_headers(client) -> dict[str, str]:
    """EPA air quality officer: national scope, responder role."""
    return {"Authorization": f"Bearer {token_for(client, EPA_USERNAME, EPA_PASSWORD)}"}


@pytest.fixture
def ohwefo_headers(client) -> dict[str, str]:
    """Ɔhwɛfoɔ: the on-ground officer for Madina who validates what citizens report."""
    return {"Authorization": f"Bearer {token_for(client, FIELD_USERNAME, FIELD_PASSWORD)}"}


@pytest.fixture
def nadmo_headers(client) -> dict[str, str]:
    """NADMO flood coordinator: scoped to Madina, responder role."""
    return {"Authorization": f"Bearer {token_for(client, NADMO_USERNAME, NADMO_PASSWORD)}"}
