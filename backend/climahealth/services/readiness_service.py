from climahealth.domain.models import RiskLevel
from climahealth.services.incident_service import (
    ReadinessReport,
    ResourceReadiness,
    hours_to_dispatch,
    readiness_status,
    required_units_for,
    worst_status,
)
from climahealth.services.models import District
from climahealth.services.ports import ReportStore, ResourceStockStore
from climahealth.services.risk_service import DistrictRiskReport, RiskService

DEMANDING_LEVELS: frozenset[RiskLevel] = frozenset({RiskLevel.HIGH, RiskLevel.SEVERE})


def earliest_onset_days(report: DistrictRiskReport) -> int:
    """The soonest any raised condition could put people in a clinic."""
    raised = [risk for risk in report.risks if risk.level in DEMANDING_LEVELS]
    if not raised:
        return 0
    return min(risk.lag_window.minimum_days for risk in raised)


class ReadinessService:
    def __init__(
        self,
        risk_service: RiskService,
        stocks: ResourceStockStore,
        reports: ReportStore,
    ) -> None:
        self._risk_service = risk_service
        self._stocks = stocks
        self._reports = reports

    def readiness_for(self, district: District) -> ReadinessReport:
        report = self._risk_service.report_for(district)
        onset_days = earliest_onset_days(report)
        resources = tuple(
            self._assess(
                stock.resource, stock.baseline_units, stock.stocked_units, report, onset_days
            )
            for stock in self._stocks.for_district(district.district_id)
        )
        deadlines = [
            item.hours_to_dispatch for item in resources if item.hours_to_dispatch is not None
        ]
        return ReadinessReport(
            district_id=district.district_id,
            district_name=district.name,
            overall_risk_level=report.overall_level,
            generated_on=report.generated_on,
            open_reports=len(self._reports.for_district(district.district_id)),
            resources=resources,
            status=worst_status(tuple(item.status for item in resources)),
            hours_to_dispatch=min(deadlines) if deadlines else None,
        )

    def _assess(
        self,
        resource: str,
        baseline_units: int,
        stocked_units: int,
        report: DistrictRiskReport,
        onset_days: int,
    ) -> ResourceReadiness:
        required = required_units_for(baseline_units, report.overall_level)
        shortfall = max(required - stocked_units, 0)
        return ResourceReadiness(
            resource=resource,
            required_units=required,
            stocked_units=stocked_units,
            status=readiness_status(required, stocked_units),
            shortfall_units=shortfall,
            hours_to_dispatch=hours_to_dispatch(shortfall, onset_days),
        )
