from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import Field

from climahealth.domain.models import ClimateFeatures, FeatureProvenance, Season
from climahealth.services.events import DomainEvent, EventType, NullEventPublisher
from climahealth.services.models import District, ServiceModel
from climahealth.services.ports import (
    ClimateOverrideStore,
    Clock,
    EventPublisher,
    SeasonOverrideStore,
)


class DemoScenario(StrEnum):
    """Reproducible climate states behind the proposal's demonstration story."""

    HEAVY_RAIN = "heavy_rain"
    DRY_AND_DUSTY = "dry_and_dusty"
    COASTAL_FLOOD = "coastal_flood"
    HARMATTAN = "harmattan"
    DROUGHT = "drought"
    HEATWAVE = "heatwave"
    CALM = "calm"


class DemoConditionsRequest(ServiceModel):
    district_id: str
    scenario: DemoScenario | None = None
    season: Season | None = None
    rainfall_7d_mm: float | None = Field(default=None, ge=0)
    rainfall_14d_mm: float | None = Field(default=None, ge=0)
    consecutive_dry_days: int | None = Field(default=None, ge=0)
    humidity_mean_percent: float | None = Field(default=None, ge=0, le=100)
    temperature_mean_c: float | None = None
    temperature_max_c: float | None = None
    dust_concentration_ug_m3: float | None = Field(default=None, ge=0)
    particulate_matter_10_ug_m3: float | None = Field(default=None, ge=0)


HEAVY_RAIN_FEATURES = {
    "rainfall_7d_mm": 120.0,
    "rainfall_14d_mm": 180.0,
    "consecutive_dry_days": 0,
    "humidity_mean_percent": 85.0,
    "temperature_mean_c": 27.0,
    "temperature_max_c": 31.0,
    "dust_concentration_ug_m3": 5.0,
    "particulate_matter_10_ug_m3": 20.0,
}

DRY_AND_DUSTY_FEATURES = {
    "rainfall_7d_mm": 0.0,
    "rainfall_14d_mm": 0.0,
    "consecutive_dry_days": 40,
    "humidity_mean_percent": 18.0,
    "temperature_mean_c": 31.0,
    "temperature_max_c": 39.0,
    "dust_concentration_ug_m3": 120.0,
    "particulate_matter_10_ug_m3": 150.0,
}

CALM_FEATURES = {
    "rainfall_7d_mm": 8.0,
    "rainfall_14d_mm": 15.0,
    "consecutive_dry_days": 4,
    "humidity_mean_percent": 55.0,
    "temperature_mean_c": 26.0,
    "temperature_max_c": 30.0,
    "dust_concentration_ug_m3": 10.0,
    "particulate_matter_10_ug_m3": 25.0,
}

# Ada East, October 2024: coastal flooding preceded the cholera outbreak that
# reached 36 districts and 6,145 suspected cases.
COASTAL_FLOOD_FEATURES = {
    "rainfall_7d_mm": 165.0,
    "rainfall_14d_mm": 240.0,
    "consecutive_dry_days": 0,
    "humidity_mean_percent": 89.0,
    "temperature_mean_c": 28.0,
    "temperature_max_c": 32.0,
    "dust_concentration_ug_m3": 3.0,
    "particulate_matter_10_ug_m3": 15.0,
}

# Tamale Metropolitan in the harmattan: the signal set behind the proposal's
# worked example in section 4.
HARMATTAN_FEATURES = {
    "rainfall_7d_mm": 0.0,
    "rainfall_14d_mm": 0.0,
    "consecutive_dry_days": 21,
    "humidity_mean_percent": 18.0,
    "temperature_mean_c": 30.0,
    "temperature_max_c": 37.0,
    "dust_concentration_ug_m3": 145.0,
    "particulate_matter_10_ug_m3": 190.0,
}

# Bawku and the northern belt: rainfall deficit feeding into nutrition risk.
DROUGHT_FEATURES = {
    "rainfall_7d_mm": 0.0,
    "rainfall_14d_mm": 4.0,
    "consecutive_dry_days": 34,
    "humidity_mean_percent": 26.0,
    "temperature_mean_c": 32.0,
    "temperature_max_c": 38.0,
    "dust_concentration_ug_m3": 55.0,
    "particulate_matter_10_ug_m3": 70.0,
}

HEATWAVE_FEATURES = {
    "rainfall_7d_mm": 2.0,
    "rainfall_14d_mm": 9.0,
    "consecutive_dry_days": 9,
    "humidity_mean_percent": 66.0,
    "temperature_mean_c": 33.0,
    "temperature_max_c": 41.0,
    "dust_concentration_ug_m3": 22.0,
    "particulate_matter_10_ug_m3": 45.0,
}

SCENARIO_FEATURES: dict[DemoScenario, dict[str, float | int]] = {
    DemoScenario.HEAVY_RAIN: HEAVY_RAIN_FEATURES,
    DemoScenario.DRY_AND_DUSTY: DRY_AND_DUSTY_FEATURES,
    DemoScenario.COASTAL_FLOOD: COASTAL_FLOOD_FEATURES,
    DemoScenario.HARMATTAN: HARMATTAN_FEATURES,
    DemoScenario.DROUGHT: DROUGHT_FEATURES,
    DemoScenario.HEATWAVE: HEATWAVE_FEATURES,
    DemoScenario.CALM: CALM_FEATURES,
}

SCENARIO_SEASONS: dict[DemoScenario, Season] = {
    DemoScenario.HEAVY_RAIN: Season.WET,
    DemoScenario.DRY_AND_DUSTY: Season.DRY,
    DemoScenario.COASTAL_FLOOD: Season.WET,
    DemoScenario.HARMATTAN: Season.DRY,
    DemoScenario.DROUGHT: Season.DRY,
    DemoScenario.HEATWAVE: Season.DRY,
}


def features_from(request: DemoConditionsRequest, observed_on: date) -> ClimateFeatures:
    base = dict(SCENARIO_FEATURES[request.scenario or DemoScenario.CALM])
    explicit = request.model_dump(exclude={"district_id", "scenario", "season"}, exclude_none=True)
    return ClimateFeatures(
        observed_on=observed_on,
        provenance=FeatureProvenance.DEMO,
        **(base | explicit),
    )


def season_from(request: DemoConditionsRequest) -> Season | None:
    if request.season is not None:
        return request.season
    if request.scenario is None:
        return None
    return SCENARIO_SEASONS.get(request.scenario)


class DemoService:
    def __init__(
        self,
        overrides: ClimateOverrideStore,
        seasons: SeasonOverrideStore,
        clock: Clock,
        events: EventPublisher | None = None,
    ) -> None:
        self._overrides = overrides
        self._seasons = seasons
        self._clock = clock
        self._events = events or NullEventPublisher()

    def set_conditions(self, district: District, request: DemoConditionsRequest) -> ClimateFeatures:
        season = season_from(request)
        if season is None:
            self._seasons.clear_season(district.district_id)
        else:
            self._seasons.set_season(district.district_id, season)
        stored = self._overrides.set_override(
            district.district_id, features_from(request, self._clock.today())
        )
        self._events.publish(
            DomainEvent(
                event_type=EventType.DISTRICT_CONDITIONS_CHANGED,
                district_id=district.district_id,
                resource_id=None,
                summary=f"Climate conditions updated for {district.name}",
                occurred_at=datetime.now(UTC),
            )
        )
        return stored

    def clear_conditions(self, district: District) -> None:
        self._overrides.clear_override(district.district_id)
        self._seasons.clear_season(district.district_id)
        self._events.publish(
            DomainEvent(
                event_type=EventType.DISTRICT_CONDITIONS_CHANGED,
                district_id=district.district_id,
                resource_id=None,
                summary=f"Climate conditions restored to live data for {district.name}",
                occurred_at=datetime.now(UTC),
            )
        )

    def clear_all(self) -> None:
        self._overrides.clear_all_overrides()
        self._seasons.clear_all_seasons()
