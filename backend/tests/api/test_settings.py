import pytest
from pydantic import ValidationError

from climahealth.api.settings import (
    DEFAULT_CORS_ORIGINS,
    DEVELOPMENT_TOKEN_SECRET,
    Settings,
    load_settings,
)

LONG_SECRET = "a-secret-that-is-definitely-long-enough-0123456789"


def settings_without_env_file(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_defaults_let_the_api_run_with_no_configuration():
    settings = settings_without_env_file()

    assert settings.token_secret == DEVELOPMENT_TOKEN_SECRET
    assert settings.cors_origins == DEFAULT_CORS_ORIGINS
    assert settings.ghana_nlp_api_key is None
    assert settings.token_lifetime_hours == 24
    assert settings.climate_cache_minutes == 30


def test_the_development_secret_is_flagged_as_such():
    assert settings_without_env_file().uses_development_token_secret is True
    assert (
        settings_without_env_file(token_secret=LONG_SECRET).uses_development_token_secret is False
    )


def test_environment_variables_are_read_with_the_project_prefix(monkeypatch):
    monkeypatch.setenv("CLIMAHEALTH_TOKEN_SECRET", LONG_SECRET)
    monkeypatch.setenv("CLIMAHEALTH_TOKEN_LIFETIME_HOURS", "3")
    monkeypatch.setenv("CLIMAHEALTH_CLIMATE_CACHE_MINUTES", "5")

    settings = settings_without_env_file()

    assert settings.token_secret == LONG_SECRET
    assert settings.token_lifetime_hours == 3
    assert settings.climate_cache_minutes == 5


def test_an_env_file_is_loaded(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"CLIMAHEALTH_TOKEN_SECRET={LONG_SECRET}\nCLIMAHEALTH_GHANA_NLP_API_KEY=khaya-key-123\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("CLIMAHEALTH_TOKEN_SECRET", raising=False)

    settings = Settings(_env_file=env_file)

    assert settings.token_secret == LONG_SECRET
    assert settings.ghana_nlp_api_key == "khaya-key-123"


def test_a_real_environment_variable_beats_the_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(f"CLIMAHEALTH_TOKEN_SECRET={LONG_SECRET}\n", encoding="utf-8")
    monkeypatch.setenv("CLIMAHEALTH_TOKEN_SECRET", "environment-wins-and-is-long-enough-x")

    assert Settings(_env_file=env_file).token_secret.startswith("environment-wins")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("http://a.test", ("http://a.test",)),
        ("http://a.test,http://b.test", ("http://a.test", "http://b.test")),
        ("http://a.test , http://b.test ", ("http://a.test", "http://b.test")),
        ("", DEFAULT_CORS_ORIGINS),
    ],
)
def test_cors_origins_accept_a_comma_separated_list(monkeypatch, raw, expected):
    if raw:
        monkeypatch.setenv("CLIMAHEALTH_CORS_ORIGINS", raw)
        assert settings_without_env_file().cors_origins == expected
    else:
        assert settings_without_env_file().cors_origins == expected


def test_a_blank_translation_key_is_treated_as_absent(monkeypatch):
    monkeypatch.setenv("CLIMAHEALTH_GHANA_NLP_API_KEY", "   ")

    assert settings_without_env_file().ghana_nlp_api_key is None


def test_a_short_token_secret_is_refused_at_startup():
    with pytest.raises(ValidationError):
        settings_without_env_file(token_secret="too-short")


def test_a_zero_token_lifetime_is_refused():
    with pytest.raises(ValidationError):
        settings_without_env_file(token_lifetime_hours=0)


def test_a_negative_cache_lifetime_is_refused():
    with pytest.raises(ValidationError):
        settings_without_env_file(climate_cache_minutes=-1)


def test_unrelated_environment_variables_are_ignored(monkeypatch):
    monkeypatch.setenv("CLIMAHEALTH_SOMETHING_UNKNOWN", "value")

    assert settings_without_env_file().token_secret == DEVELOPMENT_TOKEN_SECRET


def test_load_settings_returns_usable_settings():
    settings = load_settings()

    assert len(settings.token_secret) >= 32
    assert settings.cors_origins
