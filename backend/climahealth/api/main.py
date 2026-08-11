import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from climahealth.api.container import Container, build_container
from climahealth.api.errors import register_error_handlers
from climahealth.api.routers import (
    access,
    agency,
    alerts,
    citizens,
    districts,
    gamification,
    lessons,
    matrix,
    outreach,
    play,
    prevention,
    public,
    reports,
    risk,
    websocket,
)
from climahealth.api.settings import Settings, load_settings

API_TITLE = "ClimaHealth Predict"
API_DESCRIPTION = (
    "Climate-health early-warning API for Ghana. A deterministic rules engine turns a "
    "district's climate conditions into ranked, explained health risks."
)
API_VERSION = "0.1.0"

DEVELOPMENT_SECRET_WARNING = (
    "CLIMAHEALTH_TOKEN_SECRET is not set, so tokens are signed with the public "
    "development secret. Set it in .env before deploying."
)

logger = logging.getLogger(__name__)

ROUTERS = (
    access.router,
    districts.router,
    risk.router,
    alerts.router,
    agency.router,
    reports.router,
    gamification.router,
    citizens.router,
    lessons.router,
    matrix.router,
    outreach.router,
    play.router,
    prevention.router,
    public.router,
    websocket.router,
)


def create_app(
    container: Container | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    resolved_settings = settings or load_settings()
    if resolved_settings.uses_development_token_secret:
        logger.warning(DEVELOPMENT_SECRET_WARNING)
    app = FastAPI(title=API_TITLE, description=API_DESCRIPTION, version=API_VERSION)
    resolved_container = container or build_container(resolved_settings)
    app.state.container = resolved_container
    app.state.broadcaster = resolved_container.broadcaster

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_origins),
        allow_origin_regex=resolved_settings.development_origin_pattern,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in ROUTERS:
        app.include_router(router)

    register_error_handlers(app)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
