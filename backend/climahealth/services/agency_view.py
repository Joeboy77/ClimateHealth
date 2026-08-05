from collections.abc import Sequence

from climahealth.domain.models import HealthCondition, RiskLevel
from climahealth.services.access import AGENCY_NAMES, AGENCY_SHORT_NAMES, Agency
from climahealth.services.models import ServiceModel
from climahealth.services.playbook import CONDITION_RESPONSIBILITIES
from climahealth.services.risk_service import DistrictRiskReport

VIEW_TRIGGER_LEVELS: frozenset[RiskLevel] = frozenset({RiskLevel.HIGH, RiskLevel.SEVERE})


class AgencyFocus(ServiceModel):
    """What an agency's landing view leads with, per proposal section 8."""

    remit: str
    default_climate_layer: str
    leading_question: str


AGENCY_FOCUS: dict[Agency, AgencyFocus] = {
    Agency.GHANA_HEALTH_SERVICE: AgencyFocus(
        remit="Case forecasts, clinician alerts, clinic stock and the supply dispatch queue",
        default_climate_layer="risk",
        leading_question="Which districts will see cases, and are facilities stocked?",
    ),
    Agency.NADMO: AgencyFocus(
        remit="Flood and heat emergency risk, evacuation planning and relief deployment",
        default_climate_layer="rainfall",
        leading_question="Where is flooding driving health risk, and who must move?",
    ),
    Agency.METEOROLOGICAL_AGENCY: AgencyFocus(
        remit="How the forecast translated into health consequences and agency action",
        default_climate_layer="humidity",
        leading_question="What did this week's weather actually cause?",
    ),
    Agency.ENVIRONMENTAL_PROTECTION_AGENCY: AgencyFocus(
        remit="Air quality, dust, waste-burning and bushfire hotspots, and public advisories",
        default_climate_layer="dust",
        leading_question="Where is the air harming people, and who needs advising?",
    ),
    Agency.DISTRICT_ASSEMBLY: AgencyFocus(
        remit="Drainage, waste, water points and container-clearing operations",
        default_climate_layer="rainfall",
        leading_question="Which drains, water points and containers need work first?",
    ),
}


def conditions_for(agency: Agency) -> tuple[HealthCondition, ...]:
    """The conditions this agency holds a standing mandate for."""
    return tuple(
        condition
        for condition, responsibilities in CONDITION_RESPONSIBILITIES.items()
        if any(entry.agency is agency for entry in responsibilities)
    )


def leads_on(agency: Agency, condition: HealthCondition) -> bool:
    return any(
        entry.agency is agency and entry.is_lead
        for entry in CONDITION_RESPONSIBILITIES.get(condition, ())
    )


class AgencyConditionExposure(ServiceModel):
    condition: HealthCondition
    is_lead: bool
    districts_raised: int
    worst_level: RiskLevel
    worst_district_id: str
    worst_district_name: str


class AgencyOverview(ServiceModel):
    agency: Agency
    agency_name: str
    agency_short_name: str
    remit: str
    leading_question: str
    default_climate_layer: str
    districts_in_scope: int
    districts_needing_action: int
    exposures: tuple[AgencyConditionExposure, ...]


def focus_for(agency: Agency) -> AgencyFocus:
    return AGENCY_FOCUS[agency]


def build_overview(agency: Agency, reports: Sequence[DistrictRiskReport]) -> AgencyOverview:
    """Reduce the national picture to the conditions this agency answers for."""
    focus = focus_for(agency)
    mandate = set(conditions_for(agency))

    worst: dict[HealthCondition, tuple[RiskLevel, str, str, int]] = {}
    districts_needing_action: set[str] = set()

    severity = (RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.SEVERE)

    for report in reports:
        for risk in report.risks:
            if risk.condition not in mandate:
                continue
            if risk.level not in VIEW_TRIGGER_LEVELS:
                continue
            districts_needing_action.add(report.district.district_id)
            current = worst.get(risk.condition)
            count = (current[3] if current else 0) + 1
            if current is None or severity.index(risk.level) > severity.index(current[0]):
                worst[risk.condition] = (
                    risk.level,
                    report.district.district_id,
                    report.district.name,
                    count,
                )
            else:
                worst[risk.condition] = (current[0], current[1], current[2], count)

    exposures = tuple(
        sorted(
            (
                AgencyConditionExposure(
                    condition=condition,
                    is_lead=leads_on(agency, condition),
                    districts_raised=count,
                    worst_level=level,
                    worst_district_id=district_id,
                    worst_district_name=district_name,
                )
                for condition, (level, district_id, district_name, count) in worst.items()
            ),
            key=lambda item: (-item.districts_raised, item.condition.value),
        )
    )

    return AgencyOverview(
        agency=agency,
        agency_name=AGENCY_NAMES[agency],
        agency_short_name=AGENCY_SHORT_NAMES[agency],
        remit=focus.remit,
        leading_question=focus.leading_question,
        default_climate_layer=focus.default_climate_layer,
        districts_in_scope=len(reports),
        districts_needing_action=len(districts_needing_action),
        exposures=exposures,
    )
