from datetime import date

from climahealth.api.schemas.common import (
    ApiModel,
    ClimateSnapshotResponse,
    LagWindowResponse,
    RiskResponse,
)
from climahealth.domain.models import ConfidenceMode, RiskLevel, Season
from climahealth.services.forecast_service import CitizenForecast
from climahealth.services.narration import NarrationLanguage, WordingProvenance
from climahealth.services.risk_service import DistrictRiskReport


class RiskListResponse(ApiModel):
    district_id: str
    district_name: str
    generated_on: date
    overall_risk_level: RiskLevel
    climate: ClimateSnapshotResponse
    risks: list[RiskResponse]

    @classmethod
    def of(cls, report: DistrictRiskReport) -> "RiskListResponse":
        return cls(
            district_id=report.district.district_id,
            district_name=report.district.name,
            generated_on=report.generated_on,
            overall_risk_level=report.overall_level,
            climate=ClimateSnapshotResponse.of(report.features),
            risks=[RiskResponse.of(risk) for risk in report.risks],
        )


class ForecastRiskResponse(ApiModel):
    condition: str
    level: RiskLevel
    score: float
    lag_window: LagWindowResponse
    vulnerable_group: str
    reasons: list[str]


class ForecastResponse(ApiModel):
    district_id: str
    district_name: str
    generated_on: date
    headline: str
    summary: str
    action_today: str
    language: NarrationLanguage
    # Where the words came from. Curated wording that nobody has reviewed says so.
    wording: WordingProvenance
    confidence: ConfidenceMode
    season: Season
    climate: ClimateSnapshotResponse
    top_risks: list[ForecastRiskResponse]

    @classmethod
    def of(cls, forecast: CitizenForecast) -> "ForecastResponse":
        return cls(
            district_id=forecast.district_id,
            district_name=forecast.district_name,
            generated_on=forecast.generated_on,
            headline=forecast.headline,
            summary=forecast.summary,
            action_today=forecast.action_today,
            language=forecast.language,
            wording=forecast.wording,
            confidence=forecast.confidence,
            season=forecast.season,
            climate=ClimateSnapshotResponse.of(forecast.features),
            top_risks=[
                ForecastRiskResponse(
                    condition=risk.condition,
                    level=risk.level,
                    score=risk.score,
                    lag_window=LagWindowResponse.of(risk.lag_window),
                    vulnerable_group=risk.vulnerable_group,
                    reasons=list(risk.reasons),
                )
                for risk in forecast.top_risks
            ],
        )


class DemoConditionsResponse(ApiModel):
    district_id: str
    scenario: str | None
    climate: ClimateSnapshotResponse
    message: str
