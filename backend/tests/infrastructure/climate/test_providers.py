from datetime import date

import httpx

from climahealth.domain.engine import assess_district
from climahealth.domain.models import ClimateFeatures, FeatureProvenance
from climahealth.infrastructure.climate.open_meteo_client import OpenMeteoClient
from climahealth.infrastructure.climate.providers import (
    DemoOverrideFeatureProvider,
    OpenMeteoFeatureProvider,
)
from climahealth.infrastructure.seed.districts import MADINA, WA
from climahealth.services.models import District

WEATHER_PAYLOAD = {
    "daily": {
        "time": ["2026-07-26", "2026-07-27"],
        "precipitation_sum": [60.0, 60.0],
        "temperature_2m_mean": [27.0, 27.0],
        "temperature_2m_max": [31.0, 31.0],
    },
    "hourly": {
        "time": ["2026-07-26T00:00", "2026-07-27T00:00"],
        "relative_humidity_2m": [85.0, 85.0],
    },
}


class StubProvider:
    def __init__(self, features: ClimateFeatures) -> None:
        self.features = features
        self.calls: list[District] = []

    def features_for(self, district: District) -> ClimateFeatures:
        self.calls.append(district)
        return self.features


def live_features(**overrides: object) -> ClimateFeatures:
    defaults: dict[str, object] = {
        "observed_on": date(2026, 7, 27),
        "rainfall_7d_mm": 5.0,
        "rainfall_14d_mm": 10.0,
        "consecutive_dry_days": 3,
        "humidity_mean_percent": 55.0,
        "temperature_mean_c": 27.0,
        "temperature_max_c": 31.0,
        "dust_concentration_ug_m3": 8.0,
        "particulate_matter_10_ug_m3": 20.0,
    }
    return ClimateFeatures(**(defaults | overrides))


def test_open_meteo_provider_derives_features_for_a_district():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json=WEATHER_PAYLOAD if "air-quality" not in str(request.url) else {}
        )

    provider = OpenMeteoFeatureProvider(
        OpenMeteoClient(httpx.Client(transport=httpx.MockTransport(handler)))
    )

    features = provider.features_for(MADINA)

    assert features.rainfall_7d_mm == 120.0
    assert features.humidity_mean_percent == 85.0
    assert features.provenance is FeatureProvenance.LIVE


def test_provider_requests_the_districts_own_coordinates():
    seen: list[tuple[float, float]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (
                float(request.url.params["latitude"]),
                float(request.url.params["longitude"]),
            )
        )
        return httpx.Response(200, json=WEATHER_PAYLOAD)

    OpenMeteoFeatureProvider(
        OpenMeteoClient(httpx.Client(transport=httpx.MockTransport(handler)))
    ).features_for(WA)

    assert all(coordinates == (WA.latitude, WA.longitude) for coordinates in seen)


def test_override_replaces_upstream_features_for_that_district_only():
    upstream = StubProvider(live_features())
    provider = DemoOverrideFeatureProvider(upstream)

    provider.set_override(MADINA.district_id, live_features(rainfall_7d_mm=200.0))

    assert provider.features_for(MADINA).rainfall_7d_mm == 200.0
    assert provider.features_for(WA).rainfall_7d_mm == 5.0


def test_override_short_circuits_the_upstream_call():
    upstream = StubProvider(live_features())
    provider = DemoOverrideFeatureProvider(upstream)
    provider.set_override(MADINA.district_id, live_features())

    provider.features_for(MADINA)

    assert upstream.calls == []


def test_override_is_always_marked_as_demo_provenance():
    provider = DemoOverrideFeatureProvider(StubProvider(live_features()))

    stored = provider.set_override(
        MADINA.district_id, live_features(provenance=FeatureProvenance.LIVE)
    )

    assert stored.provenance is FeatureProvenance.DEMO
    assert provider.features_for(MADINA).provenance is FeatureProvenance.DEMO


def test_clearing_an_override_restores_upstream_features():
    upstream = StubProvider(live_features())
    provider = DemoOverrideFeatureProvider(upstream)
    provider.set_override(MADINA.district_id, live_features(rainfall_7d_mm=200.0))

    provider.clear_override(MADINA.district_id)

    assert provider.has_override(MADINA.district_id) is False
    assert provider.features_for(MADINA).rainfall_7d_mm == 5.0


def test_clear_all_overrides_resets_every_district():
    provider = DemoOverrideFeatureProvider(StubProvider(live_features()))
    provider.set_override(MADINA.district_id, live_features())
    provider.set_override(WA.district_id, live_features())

    provider.clear_all_overrides()

    assert provider.has_override(MADINA.district_id) is False
    assert provider.has_override(WA.district_id) is False


def test_override_is_indistinguishable_downstream_apart_from_provenance():
    provider = DemoOverrideFeatureProvider(StubProvider(live_features()))
    provider.set_override(
        MADINA.district_id,
        live_features(rainfall_7d_mm=120.0, rainfall_14d_mm=180.0, humidity_mean_percent=85.0),
    )

    features = provider.features_for(MADINA)
    assessments = assess_district(features, MADINA.context_on(features.observed_on))

    assert assessments[0].score > 0
    assert features.provenance is FeatureProvenance.DEMO
