from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import httpx

from climahealth.api.rate_limit import SlidingWindowLimiter
from climahealth.api.settings import Settings, load_settings
from climahealth.infrastructure.ai.caching_narrator import CachingRiskNarrator
from climahealth.infrastructure.ai.template_narrator import TemplateRiskNarrator
from climahealth.infrastructure.ai.translating_narrator import TranslatingRiskNarrator
from climahealth.infrastructure.ai.translators import (
    CachingTranslator,
    GhanaNlpTranslator,
    NoTranslation,
)
from climahealth.infrastructure.ai.twi_narrator import TwiRiskNarrator
from climahealth.infrastructure.climate.caching_provider import (
    CachingFeatureProvider,
    ClimateReadingStore,
)
from climahealth.infrastructure.climate.context_provider import (
    CalendarContextProvider,
    CommunityReportContextProvider,
    SeasonOverrideContextProvider,
)
from climahealth.infrastructure.climate.open_meteo_client import OpenMeteoClient
from climahealth.infrastructure.climate.providers import (
    DemoOverrideFeatureProvider,
    OpenMeteoFeatureProvider,
)
from climahealth.infrastructure.clock import SystemClock
from climahealth.infrastructure.database.climate_repository import PostgresClimateReadingStore
from climahealth.infrastructure.database.engine import (
    SessionFactory,
    build_engine,
    create_schema,
)
from climahealth.infrastructure.database.incident_repository import (
    PostgresActionTransitionStore,
    PostgresIncidentActionStore,
)
from climahealth.infrastructure.database.reports_repository import PostgresReportStore
from climahealth.infrastructure.events.broadcaster import InMemoryEventBroadcaster
from climahealth.infrastructure.security.passwords import Pbkdf2PasswordHasher
from climahealth.infrastructure.security.tokens import JwtTokenIssuer
from climahealth.infrastructure.seed.citizens import InMemoryCitizenStore
from climahealth.infrastructure.seed.demo_guardians import (
    DEMO_PASSWORD_SALT,
    seed_demo_guardians,
)
from climahealth.infrastructure.seed.districts import InMemoryDistrictRepository
from climahealth.infrastructure.seed.gamification import (
    InMemoryGuardianStore,
    InMemoryQuizRepository,
)
from climahealth.infrastructure.seed.incidents import (
    SEEDED_ACTIONS,
    InMemoryActionTransitionStore,
    InMemoryIncidentActionStore,
    InMemoryResourceStockStore,
)
from climahealth.infrastructure.seed.nhis import InMemoryNhisRenewalStore
from climahealth.infrastructure.seed.reports import SEEDED_REPORTS, InMemoryReportStore
from climahealth.infrastructure.seed.users import InMemoryUserRepository, seeded_users
from climahealth.infrastructure.sms.moolre import MoolreSmsSender, PreviewSmsSender
from climahealth.infrastructure.sms.sessions import InMemoryUssdSessionStore
from climahealth.infrastructure.storage.cloudinary_photos import CloudinaryPhotoStore
from climahealth.infrastructure.storage.photos import LocalPhotoStore
from climahealth.services.access_service import AccessService, ScopeGuard
from climahealth.services.alerts_service import AlertsService
from climahealth.services.citizen_service import CitizenService
from climahealth.services.demo_service import DemoService
from climahealth.services.forecast_service import ForecastService
from climahealth.services.gamification_service import GamificationService
from climahealth.services.incident_service import IncidentService
from climahealth.services.outreach_service import OutreachService
from climahealth.services.ports import (
    ActionTransitionStore,
    CitizenStore,
    IncidentActionStore,
    PhotoStore,
    ReportStore,
    Translator,
)
from climahealth.services.readiness_service import ReadinessService
from climahealth.services.reports_service import ReportsService
from climahealth.services.response_cache import StaleWhileRevalidateCache
from climahealth.services.rewards_service import RewardsService
from climahealth.services.risk_service import RiskService
from climahealth.services.tickets import InMemoryTicketStore


@dataclass(frozen=True)
class Container:
    access_service: AccessService
    scope_guard: ScopeGuard
    risk_service: RiskService
    forecast_service: ForecastService
    demo_service: DemoService
    alerts_service: AlertsService
    incident_service: IncidentService
    readiness_service: ReadinessService
    reports_service: ReportsService
    gamification_service: GamificationService
    outreach_service: OutreachService
    citizen_service: CitizenService
    rewards_service: RewardsService
    guardians: InMemoryGuardianStore
    quizzes: InMemoryQuizRepository
    broadcaster: InMemoryEventBroadcaster
    clock: SystemClock
    district_repository: InMemoryDistrictRepository
    settings: Settings
    tickets: InMemoryTicketStore
    public_limiter: SlidingWindowLimiter
    photo_store: PhotoStore
    citizen_store: CitizenStore
    response_cache: StaleWhileRevalidateCache


def build_photo_store(settings: Settings) -> PhotoStore:
    """Cloudinary when it is configured, local disk otherwise.

    A report photograph is evidence an officer needs to see from another host, so it
    belongs in object storage. Falling back to disk keeps the whole reporting flow
    working for anybody running this without a Cloudinary account.
    """
    if not settings.stores_photos_in_cloudinary:
        return LocalPhotoStore(Path(settings.photo_directory))
    return CloudinaryPhotoStore(
        cloud_name=settings.cloudinary_cloud_name or "",
        api_key=settings.cloudinary_api_key or "",
        api_secret=settings.cloudinary_api_secret or "",
        folder=settings.cloudinary_folder,
    )


def build_stores(
    settings: Settings,
) -> tuple[IncidentActionStore, ActionTransitionStore, ReportStore, ClimateReadingStore | None]:
    """Postgres when a database URL is configured, in-memory otherwise.

    The seeded demonstration rows are inserted once and then left alone, so a
    status change or a new report survives a restart.
    """
    if not settings.persists:
        return (
            InMemoryIncidentActionStore(),
            InMemoryActionTransitionStore(),
            InMemoryReportStore(),
            None,
        )

    engine = build_engine(settings.database_url or "")
    create_schema(engine)
    sessions = SessionFactory(engine)

    actions = PostgresIncidentActionStore(sessions)
    actions.seed(SEEDED_ACTIONS)
    reports = PostgresReportStore(sessions)
    reports.seed(SEEDED_REPORTS)

    return (
        actions,
        PostgresActionTransitionStore(sessions),
        reports,
        PostgresClimateReadingStore(sessions),
    )


def build_translator(settings: Settings) -> Translator:
    if settings.ghana_nlp_api_key is None:
        return NoTranslation()
    return CachingTranslator(GhanaNlpTranslator(settings.ghana_nlp_api_key, httpx.Client()))


def build_container(settings: Settings | None = None) -> Container:
    resolved_settings = settings or load_settings()
    clock = SystemClock()
    guardians = InMemoryGuardianStore()
    quizzes = InMemoryQuizRepository()
    citizen_store = InMemoryCitizenStore()
    nhis_renewals = InMemoryNhisRenewalStore()
    moolre = (
        MoolreSmsSender(
            base_url=resolved_settings.moolre_base_url,
            vaskey=resolved_settings.moolre_vaskey,
            sender_id=resolved_settings.moolre_sender_id,
        )
        if resolved_settings.moolre_vaskey
        else None
    )
    sms_sender = (
        moolre
        if resolved_settings.can_send_sms and moolre is not None
        else PreviewSmsSender(moolre)
    )
    hasher = Pbkdf2PasswordHasher()
    seed_demo_guardians(
        citizen_store,
        guardians,
        hasher.hash("seeded-demo-account", DEMO_PASSWORD_SALT),
    )


    districts = InMemoryDistrictRepository()
    scope_guard = ScopeGuard(districts)
    resource_stocks = InMemoryResourceStockStore()
    broadcaster = InMemoryEventBroadcaster()
    incident_actions, transitions, report_store, climate_store = build_stores(resolved_settings)
    users = InMemoryUserRepository(seeded_users(hasher))
    tokens = JwtTokenIssuer(
        resolved_settings.token_secret,
        lifetime=timedelta(hours=resolved_settings.token_lifetime_hours),
    )

    live_provider = CachingFeatureProvider(
        OpenMeteoFeatureProvider(OpenMeteoClient(httpx.Client())),
        lifetime=timedelta(minutes=resolved_settings.climate_cache_minutes),
        store=climate_store,
    )
    provider = DemoOverrideFeatureProvider(live_provider)
    context_provider = SeasonOverrideContextProvider(CalendarContextProvider())
    risk_context = CommunityReportContextProvider(context_provider, report_store)

    risk_service = RiskService(provider=provider, context_provider=risk_context, clock=clock)
    gamification_service = GamificationService(
        guardians=guardians,
        quizzes=quizzes,
        reports=report_store,
        risk_service=risk_service,
        clock=clock,
    )
    # Curated Twi first, machine translation second, English last. Wording written for the
    # language beats wording translated into it, and both beat leaving somebody with a
    # warning they cannot read.
    narrator = CachingRiskNarrator(
        TwiRiskNarrator(
            TranslatingRiskNarrator(TemplateRiskNarrator(), build_translator(resolved_settings))
        )
    )

    return Container(
        access_service=AccessService(users=users, tokens=tokens, hasher=hasher),
        scope_guard=scope_guard,
        risk_service=risk_service,
        forecast_service=ForecastService(risk_service=risk_service, narrator=narrator),
        demo_service=DemoService(
            overrides=provider,
            seasons=context_provider,
            clock=clock,
            events=broadcaster,
        ),
        alerts_service=AlertsService(
            risk_service=risk_service, scope_guard=scope_guard, narrator=narrator
        ),
        incident_service=IncidentService(
            risk_service=risk_service,
            actions=incident_actions,
            transitions=transitions,
            clock=clock,
            events=broadcaster,
        ),
        readiness_service=ReadinessService(
            risk_service=risk_service, stocks=resource_stocks, reports=report_store
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
            renewals=nhis_renewals,
            clock=clock,
        ),
        guardians=guardians,
        quizzes=quizzes,
        citizen_service=CitizenService(
            citizens=citizen_store,
            districts=districts,
            tokens=tokens,
            guardians=guardians,
            passwords=hasher,
        ),
        outreach_service=OutreachService(
            risk_service=risk_service,
            sms_sender=sms_sender,
            sessions=InMemoryUssdSessionStore(),
        ),
        broadcaster=broadcaster,
        clock=clock,
        district_repository=districts,
        settings=settings,
        tickets=InMemoryTicketStore(),
        public_limiter=SlidingWindowLimiter(),
        photo_store=build_photo_store(resolved_settings),
        citizen_store=citizen_store,
        response_cache=StaleWhileRevalidateCache(),
    )
