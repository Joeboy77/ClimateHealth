from collections.abc import Sequence

from climahealth.domain.models import ClimateFeatures, FeatureProvenance
from climahealth.infrastructure.climate.observations import (
    DailyObservation,
    RawClimateObservations,
)
from climahealth.services.ports import ClimateDataUnavailable

RECENT_WINDOW_DAYS = 7
EXTENDED_WINDOW_DAYS = 14
DRY_DAY_RAINFALL_THRESHOLD_MM = 1.0


def chronological(observations: Sequence[DailyObservation]) -> tuple[DailyObservation, ...]:
    return tuple(sorted(observations, key=lambda observation: observation.day))


def most_recent(
    observations: Sequence[DailyObservation], window_days: int
) -> tuple[DailyObservation, ...]:
    return tuple(observations[-window_days:])


def total_rainfall(observations: Sequence[DailyObservation]) -> float:
    return sum(observation.precipitation_mm for observation in observations)


def count_trailing_dry_days(observations: Sequence[DailyObservation]) -> int:
    dry_days = 0
    for observation in reversed(observations):
        if observation.precipitation_mm >= DRY_DAY_RAINFALL_THRESHOLD_MM:
            break
        dry_days += 1
    return dry_days


def mean_of(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def mean_of_available(values: Sequence[float | None]) -> float | None:
    available = [value for value in values if value is not None]
    if not available:
        return None
    return mean_of(available)


def derive_features(raw: RawClimateObservations) -> ClimateFeatures:
    observations = chronological(raw.observations)
    if not observations:
        raise ClimateDataUnavailable("No climate observations available for this district")

    recent = most_recent(observations, RECENT_WINDOW_DAYS)
    extended = most_recent(observations, EXTENDED_WINDOW_DAYS)

    return ClimateFeatures(
        observed_on=observations[-1].day,
        rainfall_7d_mm=total_rainfall(recent),
        rainfall_14d_mm=total_rainfall(extended),
        consecutive_dry_days=count_trailing_dry_days(observations),
        humidity_mean_percent=mean_of(
            [observation.humidity_mean_percent for observation in recent]
        ),
        temperature_mean_c=mean_of([observation.temperature_mean_c for observation in recent]),
        temperature_max_c=max(observation.temperature_max_c for observation in recent),
        dust_concentration_ug_m3=mean_of_available(
            [observation.dust_ug_m3 for observation in recent]
        ),
        particulate_matter_10_ug_m3=mean_of_available(
            [observation.particulate_matter_10_ug_m3 for observation in recent]
        ),
        provenance=FeatureProvenance.LIVE,
    )
