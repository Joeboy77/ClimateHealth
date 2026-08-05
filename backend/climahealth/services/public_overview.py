from collections.abc import Sequence
from datetime import date

from pydantic import Field

from climahealth.domain.models import HealthCondition, RiskLevel
from climahealth.services.models import ServiceModel
from climahealth.services.risk_service import DistrictRiskReport

PUBLIC_LEVELS: frozenset[RiskLevel] = frozenset({RiskLevel.HIGH, RiskLevel.SEVERE})
LISTED_DISTRICTS = 12
LISTED_CONDITIONS = 6

LEVEL_RANK: dict[RiskLevel, int] = {
    RiskLevel.LOW: 0,
    RiskLevel.MODERATE: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.SEVERE: 3,
}


class PublicDistrictRisk(ServiceModel):
    district_id: str
    district_name: str
    region: str
    level: RiskLevel
    leading_condition: HealthCondition
    score: float = Field(ge=0, le=100)
    onset_days_minimum: int = Field(ge=0)
    onset_days_maximum: int = Field(ge=0)
    vulnerable_group: str


class PublicConditionCount(ServiceModel):
    condition: HealthCondition
    districts_raised: int = Field(ge=0)
    worst_level: RiskLevel


class PublicDistrict(ServiceModel):
    """Just enough to choose where you live. No risk, no climate, no identifiers."""

    district_id: str
    name: str
    region: str


class NearestDistrict(ServiceModel):
    """The district a coordinate falls closest to, with how far that was.

    Matched against district centres rather than boundaries, which the backend does not
    hold, so a phone near a district line can be matched to its neighbour. The distance
    comes back so the app can say how firm the match is and offer to change it.
    """

    district: PublicDistrict
    distance_km: float = Field(ge=0)


class PublicOverview(ServiceModel):
    """What anyone may see without an account.

    Climate-derived risk is public-interest information: it is computed from
    open weather data against published thresholds, and a household cannot act
    on a warning it is not allowed to read. Agency workload, community reports
    and the action log stay behind the login.
    """

    generated_on: date
    districts_assessed: int = Field(ge=0)
    districts_raised: int = Field(ge=0)
    conditions: tuple[PublicConditionCount, ...]
    districts: tuple[PublicDistrictRisk, ...]


def leading_risk(report: DistrictRiskReport) -> PublicDistrictRisk | None:
    raised = [risk for risk in report.risks if risk.level in PUBLIC_LEVELS]
    if not raised:
        return None
    leading = max(raised, key=lambda risk: risk.score)
    return PublicDistrictRisk(
        district_id=report.district.district_id,
        district_name=report.district.name,
        region=report.district.region,
        level=leading.level,
        leading_condition=leading.condition,
        score=leading.score,
        onset_days_minimum=leading.lag_window.minimum_days,
        onset_days_maximum=leading.lag_window.maximum_days,
        vulnerable_group=leading.vulnerable_group,
    )


def condition_counts(
    reports: Sequence[DistrictRiskReport],
) -> tuple[PublicConditionCount, ...]:
    worst: dict[HealthCondition, RiskLevel] = {}
    counts: dict[HealthCondition, int] = {}

    for report in reports:
        for risk in report.risks:
            if risk.level not in PUBLIC_LEVELS:
                continue
            counts[risk.condition] = counts.get(risk.condition, 0) + 1
            current = worst.get(risk.condition)
            if current is None or LEVEL_RANK[risk.level] > LEVEL_RANK[current]:
                worst[risk.condition] = risk.level

    return tuple(
        sorted(
            (
                PublicConditionCount(
                    condition=condition,
                    districts_raised=count,
                    worst_level=worst[condition],
                )
                for condition, count in counts.items()
            ),
            key=lambda entry: (-entry.districts_raised, entry.condition.value),
        )
    )[:LISTED_CONDITIONS]


def build_public_overview(
    reports: Sequence[DistrictRiskReport],
    today: date,
) -> PublicOverview:
    raised = [entry for entry in (leading_risk(report) for report in reports) if entry is not None]
    ranked = sorted(
        raised,
        key=lambda entry: (-LEVEL_RANK[entry.level], -entry.score, entry.district_name),
    )

    return PublicOverview(
        generated_on=today,
        districts_assessed=len(reports),
        districts_raised=len(raised),
        conditions=condition_counts(reports),
        districts=tuple(ranked[:LISTED_DISTRICTS]),
    )
