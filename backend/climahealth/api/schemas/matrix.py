from climahealth.api.schemas.common import ApiModel, LagWindowResponse
from climahealth.domain.models import (
    ClimateDriver,
    Comparison,
    HealthCondition,
    PathwayDefinition,
    Season,
    SignalName,
)
from climahealth.domain.pathways.definitions import ALL_PATHWAYS, TIER_ONE_PATHWAYS
from climahealth.domain.signals import SIGNAL_LABELS, SIGNAL_UNITS
from climahealth.infrastructure.ai.phrasebook import CONDITION_PLAIN_NAMES
from climahealth.services.access import AGENCY_SHORT_NAMES
from climahealth.services.playbook import responsibilities_for

DRIVER_NAMES: dict[ClimateDriver, str] = {
    ClimateDriver.RAIN_FLOOD: "Heavy rainfall, flooding and stagnant water",
    ClimateDriver.EXTREME_HEAT: "Extreme heat and heatwaves",
    ClimateDriver.HARMATTAN_DUST: "Harmattan, dust and dry season",
    ClimateDriver.AIR_POLLUTION: "Air pollution from traffic, waste burning and biomass",
    ClimateDriver.DROUGHT: "Drought, erratic rainfall and food-system shocks",
}

DRIVER_ORDER: tuple[ClimateDriver, ...] = (
    ClimateDriver.RAIN_FLOOD,
    ClimateDriver.EXTREME_HEAT,
    ClimateDriver.HARMATTAN_DUST,
    ClimateDriver.AIR_POLLUTION,
    ClimateDriver.DROUGHT,
)


class TriggerResponse(ApiModel):
    signal_label: str
    comparison: Comparison
    threshold: float
    unit: str
    weight: float
    description: str


class GateResponse(ApiModel):
    permitted_seasons: list[Season]
    requires_meningitis_belt: bool
    requires_flood_prone: bool
    is_unconditional: bool


class PathwayResponse(ApiModel):
    condition: HealthCondition
    condition_label: str
    plain_name: str
    tier: int
    gate: GateResponse
    triggers: list[TriggerResponse]
    lag_window: LagWindowResponse
    vulnerable_group: str
    lead_agencies: list[str]
    supporting_agencies: list[str]


class DriverGroupResponse(ApiModel):
    driver: ClimateDriver
    driver_name: str
    pathways: list[PathwayResponse]


class MatrixResponse(ApiModel):
    condition_count: int
    driver_count: int
    signal_count: int
    drivers: list[DriverGroupResponse]


def _pathway(pathway: PathwayDefinition) -> PathwayResponse:
    responsibilities = responsibilities_for(pathway.condition)
    return PathwayResponse(
        condition=pathway.condition,
        condition_label=pathway.condition.value.replace("_", " ").capitalize(),
        plain_name=CONDITION_PLAIN_NAMES.get(pathway.condition, pathway.condition.value),
        tier=1 if pathway in TIER_ONE_PATHWAYS else 2,
        gate=GateResponse(
            permitted_seasons=list(pathway.gate.permitted_seasons),
            requires_meningitis_belt=pathway.gate.requires_meningitis_belt,
            requires_flood_prone=pathway.gate.requires_flood_prone,
            is_unconditional=(
                len(pathway.gate.permitted_seasons) == len(list(Season))
                and not pathway.gate.requires_meningitis_belt
                and not pathway.gate.requires_flood_prone
            ),
        ),
        triggers=[
            TriggerResponse(
                signal_label=SIGNAL_LABELS[trigger.signal],
                comparison=trigger.comparison,
                threshold=trigger.threshold,
                unit=SIGNAL_UNITS[trigger.signal].strip(),
                weight=trigger.weight,
                description=trigger.description,
            )
            for trigger in pathway.triggers
        ],
        lag_window=LagWindowResponse.of(pathway.lag_window),
        vulnerable_group=pathway.vulnerable_group,
        lead_agencies=[
            AGENCY_SHORT_NAMES[entry.agency] for entry in responsibilities if entry.is_lead
        ],
        supporting_agencies=[
            AGENCY_SHORT_NAMES[entry.agency] for entry in responsibilities if not entry.is_lead
        ],
    )


def build_matrix() -> MatrixResponse:
    groups = [
        DriverGroupResponse(
            driver=driver,
            driver_name=DRIVER_NAMES[driver],
            pathways=[_pathway(pathway) for pathway in ALL_PATHWAYS if pathway.driver is driver],
        )
        for driver in DRIVER_ORDER
    ]
    return MatrixResponse(
        condition_count=len(ALL_PATHWAYS),
        driver_count=len(groups),
        signal_count=len(list(SignalName)),
        drivers=groups,
    )
