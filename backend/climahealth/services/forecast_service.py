from datetime import date

from climahealth.domain.models import (
    ClimateFeatures,
    ConfidenceMode,
    LagWindow,
    RiskAssessment,
    RiskLevel,
    Season,
)
from climahealth.services.models import District, ServiceModel
from climahealth.services.narration import (
    NarrationAudience,
    NarrationLanguage,
    NarrationRequest,
    WordingProvenance,
)
from climahealth.services.ports import RiskNarrator
from climahealth.services.risk_service import RiskService

TOP_RISK_COUNT = 3


def confidence_of(risks: tuple[RiskAssessment, ...]) -> ConfidenceMode:
    if not risks:
        return ConfidenceMode.LIVE
    return risks[0].confidence


class ForecastRisk(ServiceModel):
    condition: str
    level: RiskLevel
    score: float
    lag_window: LagWindow
    vulnerable_group: str
    reasons: tuple[str, ...]


class CitizenForecast(ServiceModel):
    district_id: str
    district_name: str
    generated_on: date
    headline: str
    summary: str
    action_today: str
    language: NarrationLanguage
    wording: WordingProvenance
    confidence: ConfidenceMode
    top_risks: tuple[ForecastRisk, ...]
    # The readings the verdict was drawn from. A person wants to know whether it will
    # rain today as well as what the rain will do to them, and sending them to another
    # app for half of that is how they stop opening this one.
    features: ClimateFeatures
    season: Season


class ForecastService:
    def __init__(self, risk_service: RiskService, narrator: RiskNarrator) -> None:
        self._risk_service = risk_service
        self._narrator = narrator

    def forecast_for(
        self,
        district: District,
        audience: NarrationAudience = NarrationAudience.CITIZEN,
        language: NarrationLanguage = NarrationLanguage.ENGLISH,
    ) -> CitizenForecast:
        report = self._risk_service.report_for(district)
        top_risks = report.risks[:TOP_RISK_COUNT]

        narration = self._narrator.narrate(
            NarrationRequest(
                district_name=district.name,
                risks=top_risks,
                audience=audience,
                language=language,
            )
        )

        return CitizenForecast(
            district_id=district.district_id,
            district_name=district.name,
            generated_on=report.generated_on,
            features=report.features,
            season=report.season,
            headline=narration.headline,
            summary=narration.summary,
            action_today=narration.action_today,
            language=narration.language,
            wording=narration.wording,
            confidence=confidence_of(report.risks),
            top_risks=tuple(
                ForecastRisk(
                    condition=risk.condition.value,
                    level=risk.level,
                    score=risk.score,
                    lag_window=risk.lag_window,
                    vulnerable_group=risk.vulnerable_group,
                    reasons=risk.reasons,
                )
                for risk in top_risks
            ),
        )
