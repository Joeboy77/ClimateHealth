from datetime import date

from climahealth.domain.models import HealthCondition, LagWindow, RiskLevel
from climahealth.services.access import AuthenticatedUser
from climahealth.services.access_service import ScopeGuard
from climahealth.services.models import ServiceModel
from climahealth.services.narration import NarrationAudience, NarrationRequest
from climahealth.services.ports import RiskNarrator
from climahealth.services.risk_service import DistrictRiskReport, RiskService

ALERTING_LEVELS: frozenset[RiskLevel] = frozenset({RiskLevel.HIGH, RiskLevel.SEVERE})


class Alert(ServiceModel):
    alert_id: str
    district_id: str
    district_name: str
    region: str
    condition: HealthCondition
    level: RiskLevel
    score: float
    lag_window: LagWindow
    vulnerable_group: str
    reasons: tuple[str, ...]
    raised_on: date
    recommended_action: str


def alert_identifier(district_id: str, condition: HealthCondition, raised_on: date) -> str:
    return f"{district_id}:{condition.value}:{raised_on.isoformat()}"


class AlertsService:
    def __init__(
        self,
        risk_service: RiskService,
        scope_guard: ScopeGuard,
        narrator: RiskNarrator,
    ) -> None:
        self._risk_service = risk_service
        self._scope_guard = scope_guard
        self._narrator = narrator

    def active_alerts(self, user: AuthenticatedUser) -> tuple[Alert, ...]:
        districts = self._scope_guard.visible_districts(user)
        alerts = [
            alert
            for report in self._risk_service.reports_for(districts)
            for alert in self._alerts_from(report)
        ]
        return tuple(sorted(alerts, key=lambda alert: (-alert.score, alert.district_id)))

    def find_alert(self, user: AuthenticatedUser, alert_id: str) -> Alert | None:
        return next(
            (alert for alert in self.active_alerts(user) if alert.alert_id == alert_id),
            None,
        )

    def _alerts_from(self, report: DistrictRiskReport) -> list[Alert]:
        return [
            Alert(
                alert_id=alert_identifier(
                    report.district.district_id, risk.condition, report.generated_on
                ),
                district_id=report.district.district_id,
                district_name=report.district.name,
                region=report.district.region,
                condition=risk.condition,
                level=risk.level,
                score=risk.score,
                lag_window=risk.lag_window,
                vulnerable_group=risk.vulnerable_group,
                reasons=risk.reasons,
                raised_on=report.generated_on,
                recommended_action=self._narrator.narrate(
                    NarrationRequest(
                        district_name=report.district.name,
                        risks=(risk,),
                        audience=NarrationAudience.OFFICER,
                    )
                ).action_today,
            )
            for risk in report.risks
            if risk.level in ALERTING_LEVELS
        ]
