from enum import StrEnum
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEVELOPMENT_TOKEN_SECRET = "climahealth-development-secret-change-me"
DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
)
MINIMUM_TOKEN_SECRET_LENGTH = 32

# A phone on the same Wi-Fi reaches the API by the machine's private address, which
# changes with the network, so it cannot be listed ahead of time. This matches private
# ranges on the two development ports only, and is off unless switched on deliberately.
DEVELOPMENT_ORIGIN_PATTERN = (
    r"http://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+"
    r"|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+):(3000|8081)"
)

# The sender ID approved on the Moolre account we send through. A network rejects
# any name that is not registered, so this defaults to the one that is rather than
# to the product name, which is not.
DEFAULT_SENDER_ID = "Klare"


class SmsDelivery(StrEnum):
    """Whether composed messages actually leave the building.

    Preview is the default everywhere. Sending real SMS costs money and cannot be
    undone, so it takes an explicit setting rather than a present credential.
    """

    PREVIEW = "preview"
    LIVE = "live"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CLIMAHEALTH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    token_secret: str = Field(
        default=DEVELOPMENT_TOKEN_SECRET, min_length=MINIMUM_TOKEN_SECRET_LENGTH
    )
    token_lifetime_hours: int = Field(default=12, gt=0)
    cors_origins: Annotated[tuple[str, ...], NoDecode] = DEFAULT_CORS_ORIGINS
    ghana_nlp_api_key: str | None = None
    climate_cache_minutes: int = Field(default=30, ge=0)
    database_url: str | None = None
    moolre_base_url: str = "https://api.moolre.com"
    moolre_vaskey: str | None = None
    moolre_sender_id: str = Field(default=DEFAULT_SENDER_ID, max_length=11)
    moolre_ussd_extension: str | None = None
    sms_delivery: SmsDelivery = SmsDelivery.PREVIEW
    # Lets a phone on the same Wi-Fi reach a development server. Never enable in
    # production: it admits any private-network origin on the development ports.
    allow_local_network_origins: bool = False
    photo_directory: str = "var/report-photos"

    @property
    def development_origin_pattern(self) -> str | None:
        return DEVELOPMENT_ORIGIN_PATTERN if self.allow_local_network_origins else None

    @property
    def can_send_sms(self) -> bool:
        return self.sms_delivery is SmsDelivery.LIVE and bool(self.moolre_vaskey)

    @field_validator("database_url", mode="before")
    @classmethod
    def treat_blank_url_as_absent(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def persists(self) -> bool:
        return self.database_url is not None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def accept_comma_separated_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(origin.strip() for origin in value.split(",") if origin.strip())
        return value

    @field_validator("ghana_nlp_api_key", "moolre_vaskey", mode="before")
    @classmethod
    def treat_blank_key_as_absent(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def uses_development_token_secret(self) -> bool:
        return self.token_secret == DEVELOPMENT_TOKEN_SECRET


def load_settings() -> Settings:
    return Settings()
