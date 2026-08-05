from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Season(StrEnum):
    DRY = "dry"
    WET = "wet"


class RiskLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


class ConfidenceMode(StrEnum):
    """Which engine tier produced a risk, per proposal section 6.3.

    Provenance (live or simulated readings) is a separate field. This says how the
    answer was reached, so an agency knows how firm the ground beneath it is.
    """

    MODEL = "model"
    THRESHOLD = "threshold"
    BASELINE = "baseline"


class FeatureProvenance(StrEnum):
    LIVE = "live"
    DEMO = "demo"


class HealthCondition(StrEnum):
    MALARIA = "malaria"
    CHOLERA = "cholera"
    MENINGITIS = "meningitis"
    DIARRHOEAL_DISEASE = "diarrhoeal_disease"
    RESPIRATORY_HEAT_ILLNESS = "respiratory_heat_illness"
    DENGUE = "dengue"
    TYPHOID_FEVER = "typhoid_fever"
    SCHISTOSOMIASIS = "schistosomiasis"
    LASSA_FEVER = "lassa_fever"
    YELLOW_FEVER = "yellow_fever"
    LEPTOSPIROSIS = "leptospirosis"
    TRACHOMA = "trachoma"
    HEAT_STROKE = "heat_stroke"
    AIR_POLLUTION_CARDIORESPIRATORY = "air_pollution_cardiorespiratory"
    CHILD_UNDERNUTRITION = "child_undernutrition"
    MATERNAL_HEAT_OUTCOMES = "maternal_heat_outcomes"


class SignalName(StrEnum):
    RAINFALL_7D_MM = "rainfall_7d_mm"
    RAINFALL_14D_MM = "rainfall_14d_mm"
    CONSECUTIVE_DRY_DAYS = "consecutive_dry_days"
    HUMIDITY_MEAN_PERCENT = "humidity_mean_percent"
    TEMPERATURE_MEAN_C = "temperature_mean_c"
    TEMPERATURE_MAX_C = "temperature_max_c"
    DUST_CONCENTRATION_UG_M3 = "dust_concentration_ug_m3"
    PARTICULATE_MATTER_10_UG_M3 = "particulate_matter_10_ug_m3"
    POOR_SANITATION_INDEX = "poor_sanitation_index"
    UNSAFE_WATER_RATIO = "unsafe_water_ratio"
    STAGNANT_WATER_INDEX = "stagnant_water_index"


class ClimateDriver(StrEnum):
    """The climate driver a pathway belongs to, per proposal section 3."""

    RAIN_FLOOD = "rain_flood"
    EXTREME_HEAT = "extreme_heat"
    HARMATTAN_DUST = "harmattan_dust"
    AIR_POLLUTION = "air_pollution"
    DROUGHT = "drought"


class Comparison(StrEnum):
    AT_LEAST = "at_least"
    AT_MOST = "at_most"


class DomainModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ClimateFeatures(DomainModel):
    observed_on: date
    rainfall_7d_mm: float = Field(ge=0)
    rainfall_14d_mm: float = Field(ge=0)
    consecutive_dry_days: int = Field(ge=0)
    humidity_mean_percent: float = Field(ge=0, le=100)
    temperature_mean_c: float
    temperature_max_c: float
    dust_concentration_ug_m3: float | None = Field(default=None, ge=0)
    particulate_matter_10_ug_m3: float | None = Field(default=None, ge=0)
    provenance: FeatureProvenance = FeatureProvenance.LIVE


class DistrictContext(DomainModel):
    district_id: str
    season: Season
    in_meningitis_belt: bool = False
    flood_prone: bool = False
    coastal: bool = False
    distance_to_coast_km: float | None = Field(default=None, ge=0)
    poor_sanitation_index: float | None = Field(default=None, ge=0, le=1)
    unsafe_water_ratio: float | None = Field(default=None, ge=0, le=1)
    stagnant_water_index: float | None = Field(default=None, ge=0, le=1)

    def holds(self, condition: "ContextCondition") -> bool:
        if condition is ContextCondition.FLOOD_PRONE:
            return self.flood_prone
        return self.coastal


class LagWindow(DomainModel):
    """Delay before cases appear, in days.

    Days rather than weeks because the fast pathways matter most: cholera runs
    2 to 10 days and diarrhoeal disease 3 to 14, and a week-resolution window
    overstates both by enough to change a dispatch decision.
    """

    minimum_days: int = Field(ge=0)
    maximum_days: int = Field(ge=0)

    @property
    def minimum_weeks(self) -> int:
        return self.minimum_days // 7

    @property
    def maximum_weeks(self) -> int:
        return self.maximum_days // 7


class TriggerDefinition(DomainModel):
    """A published threshold, optionally graded by how far the signal passes it.

    `saturation` is the reading at which the condition is as bad as this trigger
    can describe. Between threshold and saturation the trigger carries part of
    its weight, so a district barely over the line does not score the same as one
    far past it. Without a saturation the trigger stays strictly binary.
    """

    signal: SignalName
    comparison: Comparison
    threshold: float
    saturation: float | None = None
    weight: float = Field(gt=0)
    description: str

    @model_validator(mode="after")
    def saturation_lies_beyond_threshold(self) -> "TriggerDefinition":
        if self.saturation is None:
            return self
        if self.comparison is Comparison.AT_LEAST and self.saturation <= self.threshold:
            raise ValueError("saturation must exceed the threshold for an at-least trigger")
        if self.comparison is Comparison.AT_MOST and self.saturation >= self.threshold:
            raise ValueError("saturation must fall below the threshold for an at-most trigger")
        return self


class GateDefinition(DomainModel):
    permitted_seasons: tuple[Season, ...] = (Season.DRY, Season.WET)
    requires_meningitis_belt: bool = False
    requires_flood_prone: bool = False


class ContextCondition(StrEnum):
    """A standing feature of a place, as opposed to a reading taken today."""

    FLOOD_PRONE = "flood_prone"
    COASTAL = "coastal"


class ContextMultiplier(DomainModel):
    condition: ContextCondition
    factor: float = Field(gt=0)
    description: str


class PathwayDefinition(DomainModel):
    condition: HealthCondition
    driver: ClimateDriver
    gate: GateDefinition
    triggers: tuple[TriggerDefinition, ...]
    multipliers: tuple[ContextMultiplier, ...] = ()
    lag_window: LagWindow
    vulnerable_group: str


class RiskAssessment(DomainModel):
    condition: HealthCondition
    level: RiskLevel
    score: float = Field(ge=0, le=100)
    lag_window: LagWindow
    vulnerable_group: str
    reasons: tuple[str, ...]
    confidence: ConfidenceMode
