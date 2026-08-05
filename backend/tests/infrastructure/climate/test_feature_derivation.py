from datetime import date, timedelta

import pytest

from climahealth.domain.models import FeatureProvenance
from climahealth.infrastructure.climate.feature_derivation import (
    count_trailing_dry_days,
    derive_features,
    mean_of_available,
)
from climahealth.infrastructure.climate.observations import (
    DailyObservation,
    RawClimateObservations,
)
from climahealth.services.ports import ClimateDataUnavailable

FIRST_DAY = date(2026, 7, 15)


def observation(offset: int, **overrides: object) -> DailyObservation:
    defaults: dict[str, object] = {
        "day": FIRST_DAY + timedelta(days=offset),
        "precipitation_mm": 0.0,
        "temperature_mean_c": 27.0,
        "temperature_max_c": 31.0,
        "humidity_mean_percent": 60.0,
        "dust_ug_m3": 10.0,
        "particulate_matter_10_ug_m3": 25.0,
    }
    return DailyObservation(**(defaults | overrides))


def raw(*observations: DailyObservation) -> RawClimateObservations:
    return RawClimateObservations(latitude=5.68, longitude=-0.17, observations=observations)


def test_rainfall_windows_sum_the_correct_number_of_days():
    features = derive_features(
        raw(*(observation(offset, precipitation_mm=10.0) for offset in range(14)))
    )

    assert features.rainfall_7d_mm == 70.0
    assert features.rainfall_14d_mm == 140.0


def test_windows_use_the_most_recent_days_not_the_earliest():
    observations = [observation(offset, precipitation_mm=100.0) for offset in range(7)]
    observations += [observation(offset, precipitation_mm=1.0) for offset in range(7, 14)]

    features = derive_features(raw(*observations))

    assert features.rainfall_7d_mm == 7.0
    assert features.rainfall_14d_mm == 707.0


def test_observations_are_sorted_before_derivation():
    observations = [observation(offset, precipitation_mm=float(offset)) for offset in range(14)]
    shuffled = observations[7:] + observations[:7]

    assert derive_features(raw(*shuffled)) == derive_features(raw(*observations))


def test_observed_on_is_the_most_recent_day():
    features = derive_features(raw(*(observation(offset) for offset in range(14))))

    assert features.observed_on == FIRST_DAY + timedelta(days=13)


@pytest.mark.parametrize(
    ("rainfall_by_day", "expected"),
    [
        ([0.0, 0.0, 0.0], 3),
        ([10.0, 0.0, 0.0], 2),
        ([0.0, 0.0, 10.0], 0),
        ([10.0, 10.0, 10.0], 0),
        ([0.0, 5.0, 0.0], 1),
        ([0.9, 0.9, 0.9], 3),
        ([1.0, 0.0, 0.0], 2),
    ],
)
def test_consecutive_dry_days_counts_backwards_from_today(rainfall_by_day, expected):
    observations = [
        observation(offset, precipitation_mm=rainfall)
        for offset, rainfall in enumerate(rainfall_by_day)
    ]

    assert count_trailing_dry_days(observations) == expected


def test_dry_day_threshold_treats_trace_rain_as_dry():
    observations = [observation(offset, precipitation_mm=0.4) for offset in range(20)]

    assert derive_features(raw(*observations)).consecutive_dry_days == 20


def test_humidity_and_temperature_average_over_the_recent_window():
    observations = [
        observation(offset, humidity_mean_percent=40.0, temperature_mean_c=20.0)
        for offset in range(7)
    ]
    observations += [
        observation(offset, humidity_mean_percent=80.0, temperature_mean_c=30.0)
        for offset in range(7, 14)
    ]

    features = derive_features(raw(*observations))

    assert features.humidity_mean_percent == 80.0
    assert features.temperature_mean_c == 30.0


def test_temperature_max_is_the_peak_of_the_recent_window():
    observations = [observation(offset, temperature_max_c=30.0) for offset in range(13)]
    observations.append(observation(13, temperature_max_c=41.5))

    assert derive_features(raw(*observations)).temperature_max_c == 41.5


def test_missing_dust_readings_yield_none_rather_than_zero():
    observations = [observation(offset, dust_ug_m3=None) for offset in range(14)]

    assert derive_features(raw(*observations)).dust_concentration_ug_m3 is None


def test_partially_missing_dust_readings_average_what_is_available():
    observations = [observation(offset, dust_ug_m3=None) for offset in range(13)]
    observations.append(observation(13, dust_ug_m3=90.0))

    assert derive_features(raw(*observations)).dust_concentration_ug_m3 == 90.0


@pytest.mark.parametrize(
    ("values", "expected"),
    [([None, None], None), ([10.0, 20.0], 15.0), ([None, 30.0], 30.0), ([], None)],
)
def test_mean_of_available(values, expected):
    assert mean_of_available(values) == expected


def test_derived_features_are_marked_as_live():
    features = derive_features(raw(observation(0)))

    assert features.provenance is FeatureProvenance.LIVE


def test_empty_observations_raise_climate_data_unavailable():
    with pytest.raises(ClimateDataUnavailable):
        derive_features(raw())


def test_a_short_history_still_derives_features():
    features = derive_features(raw(observation(0, precipitation_mm=5.0)))

    assert features.rainfall_7d_mm == 5.0
    assert features.rainfall_14d_mm == 5.0
