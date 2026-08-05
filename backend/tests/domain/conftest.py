from datetime import date

import pytest

from climahealth.domain.models import ClimateFeatures, DistrictContext, Season

OBSERVATION_DATE = date(2026, 7, 28)


def climate_features(**overrides: object) -> ClimateFeatures:
    defaults: dict[str, object] = {
        "observed_on": OBSERVATION_DATE,
        "rainfall_7d_mm": 0.0,
        "rainfall_14d_mm": 0.0,
        "consecutive_dry_days": 0,
        "humidity_mean_percent": 50.0,
        "temperature_mean_c": 27.0,
        "temperature_max_c": 31.0,
        "dust_concentration_ug_m3": 5.0,
        "particulate_matter_10_ug_m3": 20.0,
    }
    return ClimateFeatures(**(defaults | overrides))


@pytest.fixture
def madina_context() -> DistrictContext:
    return DistrictContext(
        district_id="madina",
        season=Season.WET,
        in_meningitis_belt=False,
        flood_prone=True,
        poor_sanitation_index=0.55,
        unsafe_water_ratio=0.35,
        stagnant_water_index=0.6,
    )


@pytest.fixture
def wa_context() -> DistrictContext:
    return DistrictContext(
        district_id="wa",
        season=Season.DRY,
        in_meningitis_belt=True,
        flood_prone=False,
        poor_sanitation_index=0.45,
        unsafe_water_ratio=0.5,
        stagnant_water_index=0.1,
    )


@pytest.fixture
def madina_heavy_rain() -> ClimateFeatures:
    return climate_features(
        rainfall_7d_mm=120.0,
        rainfall_14d_mm=180.0,
        consecutive_dry_days=0,
        humidity_mean_percent=85.0,
        temperature_mean_c=27.0,
        temperature_max_c=31.0,
        dust_concentration_ug_m3=5.0,
        particulate_matter_10_ug_m3=20.0,
    )


@pytest.fixture
def wa_dry_dusty() -> ClimateFeatures:
    return climate_features(
        rainfall_7d_mm=0.0,
        rainfall_14d_mm=0.0,
        consecutive_dry_days=40,
        humidity_mean_percent=18.0,
        temperature_mean_c=31.0,
        temperature_max_c=39.0,
        dust_concentration_ug_m3=120.0,
        particulate_matter_10_ug_m3=150.0,
    )
