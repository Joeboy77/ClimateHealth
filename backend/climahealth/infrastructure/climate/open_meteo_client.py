from collections.abc import Sequence
from datetime import date, datetime
from typing import Any

import httpx

from climahealth.infrastructure.climate.observations import (
    DailyObservation,
    RawClimateObservations,
)
from climahealth.services.ports import ClimateDataUnavailable

WEATHER_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_ENDPOINT = "https://air-quality-api.open-meteo.com/v1/air-quality"

OBSERVATION_WINDOW_DAYS = 14
DAILY_WEATHER_VARIABLES = "precipitation_sum,temperature_2m_max,temperature_2m_mean"
HOURLY_HUMIDITY_VARIABLE = "relative_humidity_2m"
HOURLY_AIR_QUALITY_VARIABLES = "pm10,dust"
REQUEST_TIMEOUT_SECONDS = 20.0
MAX_LOCATIONS_PER_REQUEST = 100
TOO_MANY_REQUESTS = 429


def daily_means_from_hourly(
    timestamps: Sequence[str], values: Sequence[float | None]
) -> dict[date, float]:
    totals: dict[date, list[float]] = {}
    for timestamp, value in zip(timestamps, values, strict=False):
        if value is None:
            continue
        day = datetime.fromisoformat(timestamp).date()
        totals.setdefault(day, []).append(value)
    return {day: sum(readings) / len(readings) for day, readings in totals.items()}


class OpenMeteoClient:
    def __init__(
        self,
        http_client: httpx.Client,
        observation_window_days: int = OBSERVATION_WINDOW_DAYS,
    ) -> None:
        self._http_client = http_client
        self._observation_window_days = observation_window_days

    def fetch_observations(self, latitude: float, longitude: float) -> RawClimateObservations:
        return self.fetch_many(((latitude, longitude),))[0]

    def fetch_many(
        self, coordinates: Sequence[tuple[float, float]]
    ) -> list[RawClimateObservations]:
        """Open-Meteo accepts many locations per call, which keeps a national
        sweep to a handful of requests instead of one per district."""
        if not coordinates:
            return []

        results: list[RawClimateObservations] = []
        for start in range(0, len(coordinates), MAX_LOCATIONS_PER_REQUEST):
            batch = list(coordinates[start : start + MAX_LOCATIONS_PER_REQUEST])
            weather = self._fetch_weather_batch(batch)
            air_quality = self._fetch_air_quality_batch(batch)
            for index, (latitude, longitude) in enumerate(batch):
                results.append(
                    RawClimateObservations(
                        latitude=latitude,
                        longitude=longitude,
                        observations=self._merge(
                            weather[index],
                            air_quality[index] if index < len(air_quality) else {},
                        ),
                    )
                )
        return results

    def _as_list(self, payload: object, expected: int) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            return [payload]
        return [{} for _ in range(expected)]

    def _fetch_weather_batch(self, batch: Sequence[tuple[float, float]]) -> list[dict[str, Any]]:
        payload = self._request(
            WEATHER_ENDPOINT,
            batch,
            {
                "daily": DAILY_WEATHER_VARIABLES,
                "hourly": HOURLY_HUMIDITY_VARIABLE,
            },
            required=True,
        )
        entries = self._as_list(payload, len(batch))
        if len(entries) != len(batch):
            raise ClimateDataUnavailable(
                f"Open-Meteo returned {len(entries)} results for {len(batch)} locations"
            )
        return entries

    def _fetch_air_quality_batch(
        self, batch: Sequence[tuple[float, float]]
    ) -> list[dict[str, Any]]:
        payload = self._request(
            AIR_QUALITY_ENDPOINT,
            batch,
            {"hourly": HOURLY_AIR_QUALITY_VARIABLES},
            required=False,
        )
        if payload is None:
            return [{} for _ in batch]
        entries = self._as_list(payload, len(batch))
        if len(entries) != len(batch):
            return [{} for _ in batch]
        return entries

    def _request(
        self,
        endpoint: str,
        batch: Sequence[tuple[float, float]],
        variables: dict[str, str],
        required: bool,
    ) -> object:
        params = {
            "latitude": ",".join(str(latitude) for latitude, _ in batch),
            "longitude": ",".join(str(longitude) for _, longitude in batch),
            "past_days": self._observation_window_days,
            "forecast_days": 1,
            "timezone": "UTC",
            **variables,
        }
        try:
            response = self._http_client.get(
                endpoint, params=params, timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            if required:
                raise ClimateDataUnavailable(f"Open-Meteo request failed: {error}") from error
            return None
        return response.json()

    def _merge(
        self, weather: dict[str, Any], air_quality: dict[str, Any]
    ) -> tuple[DailyObservation, ...]:
        daily = weather.get("daily")
        if not daily or not daily.get("time"):
            raise ClimateDataUnavailable("Open-Meteo returned no daily weather data")

        hourly = weather.get("hourly", {})
        humidity_by_day = daily_means_from_hourly(
            hourly.get("time", []), hourly.get(HOURLY_HUMIDITY_VARIABLE, [])
        )

        air_hourly = air_quality.get("hourly", {})
        dust_by_day = daily_means_from_hourly(
            air_hourly.get("time", []), air_hourly.get("dust", [])
        )
        pm10_by_day = daily_means_from_hourly(
            air_hourly.get("time", []), air_hourly.get("pm10", [])
        )

        observations = []
        for index, day_text in enumerate(daily["time"]):
            day = date.fromisoformat(day_text)
            precipitation = daily["precipitation_sum"][index]
            temperature_mean = daily["temperature_2m_mean"][index]
            temperature_max = daily["temperature_2m_max"][index]
            humidity = humidity_by_day.get(day)
            if None in (precipitation, temperature_mean, temperature_max) or humidity is None:
                continue
            observations.append(
                DailyObservation(
                    day=day,
                    precipitation_mm=precipitation,
                    temperature_mean_c=temperature_mean,
                    temperature_max_c=temperature_max,
                    humidity_mean_percent=humidity,
                    dust_ug_m3=dust_by_day.get(day),
                    particulate_matter_10_ug_m3=pm10_by_day.get(day),
                )
            )

        if not observations:
            raise ClimateDataUnavailable("Open-Meteo returned no usable daily observations")
        return tuple(observations)
