from datetime import date

from climahealth.domain.engine import assess_district
from climahealth.domain.models import ClimateFeatures, RiskAssessment, RiskLevel, Season
from climahealth.services.batching import batch_features
from climahealth.services.community_signals import CommunitySignals
from climahealth.services.models import District, ServiceModel
from climahealth.services.ports import (
    ClimateFeatureProvider,
    Clock,
    DistrictContextProvider,
)

RISK_LEVEL_SEVERITY: tuple[RiskLevel, ...] = (
    RiskLevel.LOW,
    RiskLevel.MODERATE,
    RiskLevel.HIGH,
    RiskLevel.SEVERE,
)


def highest_level(risks: tuple[RiskAssessment, ...]) -> RiskLevel:
    if not risks:
        return RiskLevel.LOW
    return max(risks, key=lambda risk: RISK_LEVEL_SEVERITY.index(risk.level)).level


class DistrictRiskReport(ServiceModel):
    district: District
    features: ClimateFeatures
    season: Season
    risks: tuple[RiskAssessment, ...]
    overall_level: RiskLevel
    generated_on: date
    community_signals: CommunitySignals | None = None


class RiskService:
    def __init__(
        self,
        provider: ClimateFeatureProvider,
        context_provider: DistrictContextProvider,
        clock: Clock,
    ) -> None:
        self._provider = provider
        self._context_provider = context_provider
        self._clock = clock

    def report_for(self, district: District) -> DistrictRiskReport:
        today = self._clock.today()
        features = self._provider.features_for(district)
        context = self._context_provider.context_for(district, today)
        risks = assess_district(features, context)
        return DistrictRiskReport(
            district=district,
            features=features,
            season=context.season,
            risks=risks,
            overall_level=highest_level(risks),
            generated_on=today,
            community_signals=self._community_signals(district, today),
        )

    def _community_signals(self, district: District, day: date) -> CommunitySignals | None:
        reader = getattr(self._context_provider, "signals_for", None)
        return reader(district, day) if callable(reader) else None

    def reports_for(self, districts: tuple[District, ...]) -> tuple[DistrictRiskReport, ...]:
        """One batched climate fetch for the whole set, not one call per district."""
        if not districts:
            return ()

        today = self._clock.today()
        features_by_district = batch_features(self._provider, districts)

        reports = []
        for district in districts:
            features = features_by_district.get(district.district_id)
            if features is None:
                continue
            context = self._context_provider.context_for(district, today)
            risks = assess_district(features, context)
            reports.append(
                DistrictRiskReport(
                    district=district,
                    features=features,
                    season=context.season,
                    risks=risks,
                    overall_level=highest_level(risks),
                    generated_on=today,
                    community_signals=self._community_signals(district, today),
                )
            )
        return tuple(reports)
