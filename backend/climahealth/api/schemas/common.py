from datetime import date

from pydantic import BaseModel

from climahealth.domain.models import (
    ClimateFeatures,
    ConfidenceMode,
    FeatureProvenance,
    LagWindow,
    RiskAssessment,
    RiskLevel,
    Season,
)
from climahealth.services.models import District


class ApiModel(BaseModel):
    pass


class LagWindowResponse(ApiModel):
    minimum_days: int
    maximum_days: int

    @classmethod
    def of(cls, lag_window: LagWindow) -> "LagWindowResponse":
        return cls(
            minimum_days=lag_window.minimum_days,
            maximum_days=lag_window.maximum_days,
        )


class RiskResponse(ApiModel):
    condition: str
    level: RiskLevel
    score: float
    lag_window: LagWindowResponse
    vulnerable_group: str
    reasons: list[str]
    confidence: ConfidenceMode

    @classmethod
    def of(cls, risk: RiskAssessment) -> "RiskResponse":
        return cls(
            condition=risk.condition.value,
            level=risk.level,
            score=risk.score,
            lag_window=LagWindowResponse.of(risk.lag_window),
            vulnerable_group=risk.vulnerable_group,
            reasons=list(risk.reasons),
            confidence=risk.confidence,
        )


class ClimateSnapshotResponse(ApiModel):
    observed_on: date
    rainfall_7d_mm: float
    rainfall_14d_mm: float
    consecutive_dry_days: int
    humidity_mean_percent: float
    temperature_mean_c: float
    temperature_max_c: float
    dust_concentration_ug_m3: float | None
    particulate_matter_10_ug_m3: float | None
    provenance: FeatureProvenance

    @classmethod
    def of(cls, features: ClimateFeatures) -> "ClimateSnapshotResponse":
        return cls(**features.model_dump())


class DistrictSummaryResponse(ApiModel):
    district_id: str
    name: str
    region: str
    latitude: float
    longitude: float
    in_meningitis_belt: bool
    overall_risk_level: RiskLevel
    leading_condition: str | None
    generated_on: date
    season: Season
    climate: ClimateSnapshotResponse


class CommunitySignalResponse(ApiModel):
    signal: str
    label: str
    value: float
    report_count: int
    newest_report_on: date


COMMUNITY_SIGNAL_LABELS: dict[str, str] = {
    "stagnant_water_index": "Standing water",
    "unsafe_water_ratio": "Unsafe drinking water",
    "poor_sanitation_index": "Sanitation deficit",
}


class DistrictDetailResponse(ApiModel):
    district_id: str
    name: str
    region: str
    latitude: float
    longitude: float
    in_meningitis_belt: bool
    season: Season
    overall_risk_level: RiskLevel
    generated_on: date
    climate: ClimateSnapshotResponse
    risks: list[RiskResponse]
    community_signals: list[CommunitySignalResponse]


def district_identity(district: District) -> dict[str, object]:
    return {
        "district_id": district.district_id,
        "name": district.name,
        "region": district.region,
        "latitude": district.latitude,
        "longitude": district.longitude,
        "in_meningitis_belt": district.in_meningitis_belt,
    }
