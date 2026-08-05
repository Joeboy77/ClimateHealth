from climahealth.domain.models import HealthCondition
from climahealth.services.access import Agency
from climahealth.services.models import ServiceModel


class Responsibility(ServiceModel):
    """What one agency does when a given condition is rising.

    These are standing mandates, not assignments. An agency does not wait to be
    told: when the engine raises a condition, every agency with a mandate for it
    already has its task.
    """

    agency: Agency
    is_lead: bool
    task: str


CONDITION_RESPONSIBILITIES: dict[HealthCondition, tuple[Responsibility, ...]] = {
    HealthCondition.MALARIA: (
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=True,
            task=(
                "Pre-position rapid diagnostic tests and ACT, and brief community health volunteers"
            ),
        ),
        Responsibility(
            agency=Agency.DISTRICT_ASSEMBLY,
            is_lead=False,
            task="Clear standing water and unblock drains in settled areas",
        ),
    ),
    HealthCondition.CHOLERA: (
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=True,
            task=(
                "Stage cholera kits and oral rehydration supplies, and put the rapid "
                "response team on standby"
            ),
        ),
        Responsibility(
            agency=Agency.DISTRICT_ASSEMBLY,
            is_lead=True,
            task="Test and chlorinate public water points, and clear refuse from drainage",
        ),
        Responsibility(
            agency=Agency.NADMO,
            is_lead=False,
            task="Identify flood-exposed communities and prepare relocation points",
        ),
    ),
    HealthCondition.MENINGITIS: (
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=True,
            task="Confirm vaccine and ceftriaxone stock, and alert clinicians to case definitions",
        ),
        Responsibility(
            agency=Agency.METEOROLOGICAL_AGENCY,
            is_lead=False,
            task="Issue harmattan dust forecasts to district health teams",
        ),
        Responsibility(
            agency=Agency.ENVIRONMENTAL_PROTECTION_AGENCY,
            is_lead=False,
            task="Suppress dust on unpaved routes and monitor particulate levels",
        ),
    ),
    HealthCondition.DIARRHOEAL_DISEASE: (
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=True,
            task="Stock oral rehydration salts and zinc at every facility",
        ),
        Responsibility(
            agency=Agency.DISTRICT_ASSEMBLY,
            is_lead=False,
            task="Inspect water points and enforce refuse collection",
        ),
    ),
    HealthCondition.RESPIRATORY_HEAT_ILLNESS: (
        Responsibility(
            agency=Agency.ENVIRONMENTAL_PROTECTION_AGENCY,
            is_lead=True,
            task="Step up air quality monitoring and publish daily readings",
        ),
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=False,
            task="Ensure clinics hold salbutamol and oxygen",
        ),
    ),
    HealthCondition.DENGUE: (
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=True,
            task="Brief clinicians to consider dengue on a negative malaria test",
        ),
        Responsibility(
            agency=Agency.DISTRICT_ASSEMBLY,
            is_lead=True,
            task="Run container-clearing sweeps in dense settlements",
        ),
    ),
    HealthCondition.TYPHOID_FEVER: (
        Responsibility(
            agency=Agency.DISTRICT_ASSEMBLY,
            is_lead=True,
            task="Sample and treat public water points, and trace shared sources",
        ),
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=False,
            task="Stock azithromycin and brief facilities on case definitions",
        ),
    ),
    HealthCondition.SCHISTOSOMIASIS: (
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=True,
            task="Schedule praziquantel administration for school-age children",
        ),
        Responsibility(
            agency=Agency.ENVIRONMENTAL_PROTECTION_AGENCY,
            is_lead=False,
            task="Survey affected water bodies and mark high-contact sites",
        ),
    ),
    HealthCondition.LASSA_FEVER: (
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=True,
            task="Ready isolation capacity, confirm ribavirin stock, and brief on VHF protocols",
        ),
        Responsibility(
            agency=Agency.DISTRICT_ASSEMBLY,
            is_lead=False,
            task="Run rodent control around markets and grain stores",
        ),
    ),
    HealthCondition.YELLOW_FEVER: (
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=True,
            task="Review vaccination coverage and prepare a reactive campaign",
        ),
    ),
    HealthCondition.LEPTOSPIROSIS: (
        Responsibility(
            agency=Agency.NADMO,
            is_lead=True,
            task="Warn flood-exposed workers and communities against wading",
        ),
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=False,
            task="Stock doxycycline and brief clinicians on fever with jaundice",
        ),
    ),
    HealthCondition.TRACHOMA: (
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=True,
            task="Plan azithromycin distribution and school screening",
        ),
        Responsibility(
            agency=Agency.DISTRICT_ASSEMBLY,
            is_lead=False,
            task="Improve water access for face washing at schools",
        ),
        Responsibility(
            agency=Agency.ENVIRONMENTAL_PROTECTION_AGENCY,
            is_lead=False,
            task="Suppress dust around schools and settlements",
        ),
    ),
    HealthCondition.CHILD_UNDERNUTRITION: (
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=True,
            task=(
                "Pre-position ready-to-use therapeutic food and surge growth "
                "monitoring at community clinics"
            ),
        ),
        Responsibility(
            agency=Agency.NADMO,
            is_lead=False,
            task="Assess household food stocks and prepare relief distribution",
        ),
        Responsibility(
            agency=Agency.DISTRICT_ASSEMBLY,
            is_lead=False,
            task="Coordinate school feeding continuity and safe water access",
        ),
    ),
    HealthCondition.MATERNAL_HEAT_OUTCOMES: (
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=True,
            task=(
                "Advise antenatal clinics on heat counselling and bring forward "
                "appointments for women in late pregnancy"
            ),
        ),
        Responsibility(
            agency=Agency.METEOROLOGICAL_AGENCY,
            is_lead=False,
            task="Issue heat warnings targeted at pregnant women and outdoor workers",
        ),
    ),
    HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY: (
        Responsibility(
            agency=Agency.ENVIRONMENTAL_PROTECTION_AGENCY,
            is_lead=True,
            task=(
                "Publish hourly air quality readings and issue a public advisory for "
                "the affected communities"
            ),
        ),
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=False,
            task=(
                "Ready inhalers and oxygen, and alert clinicians to cardiorespiratory presentations"
            ),
        ),
        Responsibility(
            agency=Agency.DISTRICT_ASSEMBLY,
            is_lead=False,
            task="Halt open waste burning and enforce against roadside burning",
        ),
    ),
    HealthCondition.HEAT_STROKE: (
        Responsibility(
            agency=Agency.METEOROLOGICAL_AGENCY,
            is_lead=True,
            task="Issue a public heat advisory with daily peak forecasts",
        ),
        Responsibility(
            agency=Agency.GHANA_HEALTH_SERVICE,
            is_lead=False,
            task="Extend clinic hours and prepare cooling and rehydration",
        ),
    ),
}


def responsibilities_for(condition: HealthCondition) -> tuple[Responsibility, ...]:
    return CONDITION_RESPONSIBILITIES.get(condition, ())


def agencies_with_a_mandate() -> frozenset[Agency]:
    return frozenset(
        responsibility.agency
        for responsibilities in CONDITION_RESPONSIBILITIES.values()
        for responsibility in responsibilities
    )
