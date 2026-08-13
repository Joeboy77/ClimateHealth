from fastapi import APIRouter

from climahealth.api.dependencies import ContainerDependency, CurrentUser, PermittedDistrict
from climahealth.api.schemas.common import (
    COMMUNITY_SIGNAL_LABELS,
    ClimateSnapshotResponse,
    CommunitySignalResponse,
    DistrictDetailResponse,
    DistrictSummaryResponse,
    RiskResponse,
    district_identity,
)
from climahealth.services.risk_service import DistrictRiskReport

router = APIRouter(tags=["districts"])


def summarise(report: DistrictRiskReport) -> DistrictSummaryResponse:
    leading = report.risks[0] if report.risks else None
    return DistrictSummaryResponse(
        **district_identity(report.district),
        overall_risk_level=report.overall_level,
        leading_condition=leading.condition.value if leading else None,
        generated_on=report.generated_on,
        season=report.season,
        climate=ClimateSnapshotResponse.of(report.features),
    )


def detail(report: DistrictRiskReport) -> DistrictDetailResponse:
    return DistrictDetailResponse(
        **district_identity(report.district),
        season=report.season,
        overall_risk_level=report.overall_level,
        generated_on=report.generated_on,
        climate=ClimateSnapshotResponse.of(report.features),
        risks=[RiskResponse.of(risk) for risk in report.risks],
        community_signals=[
            CommunitySignalResponse(
                signal=signal.signal,
                label=COMMUNITY_SIGNAL_LABELS.get(signal.signal, signal.signal),
                value=signal.value,
                report_count=signal.report_count,
                newest_report_on=signal.newest_report_on,
            )
            for signal in (report.community_signals.signals if report.community_signals else ())
        ],
    )


@router.get("/districts", response_model=list[DistrictSummaryResponse])
def list_districts(
    user: CurrentUser, container: ContainerDependency
) -> list[DistrictSummaryResponse]:
    """List districts visible to the caller with their overall risk level.

    Served from the last computed answer so nobody waits on a national sweep. If it
    has gone stale it is recomputed behind this response, not in front of it.
    """
    visible = container.scope_guard.visible_districts(user)
    key = f"districts:{user.scope.level.value}:{user.scope.district_id or 'all'}"
    return container.response_cache.get_or_compute(
        key,
        lambda: [summarise(report) for report in container.risk_service.reports_for(visible)],
    )


@router.get("/districts/{district_id}", response_model=DistrictDetailResponse)
def get_district(
    district: PermittedDistrict, container: ContainerDependency
) -> DistrictDetailResponse:
    """Return a district's climate snapshot and full ranked risk list."""
    return detail(container.risk_service.report_for(district))
