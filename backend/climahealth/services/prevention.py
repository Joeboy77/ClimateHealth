from collections.abc import Sequence
from datetime import date
from enum import StrEnum

from pydantic import Field

from climahealth.services.incident_service import ActionStatus, IncidentAction
from climahealth.services.models import District, ServiceModel

MINIMUM_ACTIONS_FOR_DISTINCTION = 3
EXEMPLARY_ON_TIME_RATE = 0.9
RELIABLE_ON_TIME_RATE = 0.7


class Distinction(StrEnum):
    """How reliably a district closed its mandated actions before onset."""

    UNRATED = "unrated"
    RESPONDING = "responding"
    RELIABLE = "reliable"
    EXEMPLARY = "exemplary"


class AvertedHazard(ServiceModel):
    """A hazard where every mandated lead action closed before onset.

    Averted means the mandated response completed inside the lag window, not a
    claim about cases that did not happen. The distinction matters: the platform
    can evidence the response, never the counterfactual.
    """

    condition: str
    lead_actions: int = Field(ge=1)
    closed_on: date


class DistrictPreventionRecord(ServiceModel):
    district_id: str
    district_name: str
    region: str
    distinction: Distinction
    actions_total: int = Field(ge=0)
    actions_complete: int = Field(ge=0)
    actions_on_time: int = Field(ge=0)
    actions_overdue: int = Field(ge=0)
    on_time_rate: float = Field(ge=0, le=1)
    averted_hazards: tuple[AvertedHazard, ...] = ()

    @property
    def outbreaks_averted(self) -> int:
        return len(self.averted_hazards)


class PreventionLeaderboard(ServiceModel):
    generated_on: date
    districts_assessed: int = Field(ge=0)
    outbreaks_averted: int = Field(ge=0)
    records: tuple[DistrictPreventionRecord, ...]


def completed_on_time(action: IncidentAction) -> bool:
    if action.status is not ActionStatus.COMPLETE or action.updated_at is None:
        return False
    return action.updated_at.date() <= action.due_on


def is_overdue(action: IncidentAction, today: date) -> bool:
    return action.status is not ActionStatus.COMPLETE and today > action.due_on


def distinction_for(actions_total: int, on_time_rate: float) -> Distinction:
    if actions_total < MINIMUM_ACTIONS_FOR_DISTINCTION:
        return Distinction.UNRATED
    if on_time_rate >= EXEMPLARY_ON_TIME_RATE:
        return Distinction.EXEMPLARY
    if on_time_rate >= RELIABLE_ON_TIME_RATE:
        return Distinction.RELIABLE
    return Distinction.RESPONDING


def averted_hazards_in(actions: Sequence[IncidentAction]) -> tuple[AvertedHazard, ...]:
    grouped: dict[str, list[IncidentAction]] = {}
    for action in actions:
        if not action.is_lead or action.source_condition is None:
            continue
        grouped.setdefault(action.source_condition, []).append(action)

    averted = []
    for condition, entries in sorted(grouped.items()):
        if not all(completed_on_time(entry) for entry in entries):
            continue
        closed = max(entry.updated_at for entry in entries if entry.updated_at is not None)
        averted.append(
            AvertedHazard(
                condition=condition,
                lead_actions=len(entries),
                closed_on=closed.date(),
            )
        )
    return tuple(averted)


def build_record(
    district: District,
    actions: Sequence[IncidentAction],
    today: date,
) -> DistrictPreventionRecord:
    total = len(actions)
    on_time = sum(1 for action in actions if completed_on_time(action))
    rate = on_time / total if total else 0.0

    return DistrictPreventionRecord(
        district_id=district.district_id,
        district_name=district.name,
        region=district.region,
        distinction=distinction_for(total, rate),
        actions_total=total,
        actions_complete=sum(1 for action in actions if action.status is ActionStatus.COMPLETE),
        actions_on_time=on_time,
        actions_overdue=sum(1 for action in actions if is_overdue(action, today)),
        on_time_rate=round(rate, 3),
        averted_hazards=averted_hazards_in(actions),
    )


DISTINCTION_RANK: dict[Distinction, int] = {
    Distinction.EXEMPLARY: 3,
    Distinction.RELIABLE: 2,
    Distinction.RESPONDING: 1,
    Distinction.UNRATED: 0,
}


def build_leaderboard(
    districts: Sequence[District],
    actions_by_district: dict[str, tuple[IncidentAction, ...]],
    today: date,
) -> PreventionLeaderboard:
    records = tuple(
        sorted(
            (
                build_record(district, actions_by_district.get(district.district_id, ()), today)
                for district in districts
            ),
            key=lambda record: (
                -DISTINCTION_RANK[record.distinction],
                -record.outbreaks_averted,
                -record.on_time_rate,
                record.district_name,
            ),
        )
    )

    return PreventionLeaderboard(
        generated_on=today,
        districts_assessed=sum(1 for record in records if record.actions_total > 0),
        outbreaks_averted=sum(record.outbreaks_averted for record in records),
        records=records,
    )
