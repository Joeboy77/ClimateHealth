from datetime import date

import httpx
import pytest

from climahealth.infrastructure.climate.open_meteo_client import (
    AIR_QUALITY_ENDPOINT,
    WEATHER_ENDPOINT,
    OpenMeteoClient,
    daily_means_from_hourly,
)
from climahealth.services.ports import ClimateDataUnavailable

WEATHER_PAYLOAD = {
    "daily": {
        "time": ["2026-07-26", "2026-07-27"],
        "precipitation_sum": [12.0, 4.0],
        "temperature_2m_mean": [27.0, 28.0],
        "temperature_2m_max": [31.0, 33.0],
    },
    "hourly": {
        "time": ["2026-07-26T00:00", "2026-07-26T12:00", "2026-07-27T00:00"],
        "relative_humidity_2m": [80.0, 90.0, 70.0],
    },
}

AIR_QUALITY_PAYLOAD = {
    "hourly": {
        "time": ["2026-07-26T00:00", "2026-07-26T12:00", "2026-07-27T00:00"],
        "pm10": [40.0, 60.0, 100.0],
        "dust": [10.0, 30.0, 55.0],
    }
}


def transport_returning(weather: dict | None, air_quality: dict | None) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host in httpx.URL(WEATHER_ENDPOINT).host:
            if weather is None:
                return httpx.Response(503)
            return httpx.Response(200, json=weather)
        if air_quality is None:
            return httpx.Response(503)
        return httpx.Response(200, json=air_quality)

    return httpx.MockTransport(handler)


def client_for(weather: dict | None, air_quality: dict | None) -> OpenMeteoClient:
    return OpenMeteoClient(httpx.Client(transport=transport_returning(weather, air_quality)))


def test_hourly_readings_are_averaged_into_daily_means():
    means = daily_means_from_hourly(
        ["2026-07-26T00:00", "2026-07-26T12:00", "2026-07-27T00:00"], [80.0, 90.0, 70.0]
    )

    assert means == {date(2026, 7, 26): 85.0, date(2026, 7, 27): 70.0}


def test_none_hourly_readings_are_skipped_when_averaging():
    means = daily_means_from_hourly(["2026-07-26T00:00", "2026-07-26T12:00"], [None, 90.0])

    assert means == {date(2026, 7, 26): 90.0}


def test_weather_and_air_quality_are_merged_into_daily_observations():
    raw = client_for(WEATHER_PAYLOAD, AIR_QUALITY_PAYLOAD).fetch_observations(5.68, -0.17)

    assert len(raw.observations) == 2
    first = raw.observations[0]
    assert first.day == date(2026, 7, 26)
    assert first.precipitation_mm == 12.0
    assert first.humidity_mean_percent == 85.0
    assert first.dust_ug_m3 == 20.0
    assert first.particulate_matter_10_ug_m3 == 50.0


def test_coordinates_are_carried_through():
    raw = client_for(WEATHER_PAYLOAD, AIR_QUALITY_PAYLOAD).fetch_observations(10.06, -2.5)

    assert (raw.latitude, raw.longitude) == (10.06, -2.5)


def test_air_quality_failure_degrades_gracefully_to_missing_dust():
    raw = client_for(WEATHER_PAYLOAD, None).fetch_observations(5.68, -0.17)

    assert all(observation.dust_ug_m3 is None for observation in raw.observations)
    assert all(observation.particulate_matter_10_ug_m3 is None for observation in raw.observations)
    assert len(raw.observations) == 2


def test_weather_failure_raises_climate_data_unavailable():
    with pytest.raises(ClimateDataUnavailable):
        client_for(None, AIR_QUALITY_PAYLOAD).fetch_observations(5.68, -0.17)


def test_empty_daily_block_raises_climate_data_unavailable():
    with pytest.raises(ClimateDataUnavailable):
        client_for({"daily": {"time": []}}, AIR_QUALITY_PAYLOAD).fetch_observations(5.68, -0.17)


def test_days_with_null_weather_values_are_dropped():
    payload = {
        "daily": {
            "time": ["2026-07-26", "2026-07-27"],
            "precipitation_sum": [None, 4.0],
            "temperature_2m_mean": [27.0, 28.0],
            "temperature_2m_max": [31.0, 33.0],
        },
        "hourly": WEATHER_PAYLOAD["hourly"],
    }

    raw = client_for(payload, AIR_QUALITY_PAYLOAD).fetch_observations(5.68, -0.17)

    assert [observation.day for observation in raw.observations] == [date(2026, 7, 27)]


def test_days_without_humidity_coverage_are_dropped():
    payload = {
        "daily": WEATHER_PAYLOAD["daily"],
        "hourly": {"time": ["2026-07-27T00:00"], "relative_humidity_2m": [70.0]},
    }

    raw = client_for(payload, AIR_QUALITY_PAYLOAD).fetch_observations(5.68, -0.17)

    assert [observation.day for observation in raw.observations] == [date(2026, 7, 27)]


def test_all_days_unusable_raises_climate_data_unavailable():
    payload = {
        "daily": WEATHER_PAYLOAD["daily"],
        "hourly": {"time": [], "relative_humidity_2m": []},
    }

    with pytest.raises(ClimateDataUnavailable):
        client_for(payload, AIR_QUALITY_PAYLOAD).fetch_observations(5.68, -0.17)


def test_requests_target_the_documented_open_meteo_endpoints():
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        payload = (
            WEATHER_PAYLOAD
            if request.url.host == httpx.URL(WEATHER_ENDPOINT).host
            else AIR_QUALITY_PAYLOAD
        )
        return httpx.Response(200, json=payload)

    OpenMeteoClient(httpx.Client(transport=httpx.MockTransport(handler))).fetch_observations(
        5.68, -0.17
    )

    assert any(url.startswith(WEATHER_ENDPOINT) for url in requested)
    assert any(url.startswith(AIR_QUALITY_ENDPOINT) for url in requested)
    assert all("past_days=14" in url for url in requested)
