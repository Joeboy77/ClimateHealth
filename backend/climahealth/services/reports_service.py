from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import Field

from climahealth.services.access import AuthenticatedUser, DistrictAccessDenied
from climahealth.services.access_service import ScopeGuard
from climahealth.services.events import DomainEvent, EventType, NullEventPublisher
from climahealth.services.models import ServiceModel
from climahealth.services.ports import Clock, EventPublisher, ReportStore


class VerificationStatus(StrEnum):
    """Proposal section 14: points and signals come from verified reports, never
    submitted ones, because paying per submission is how false reports are made.
    """

    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ReportPriority(StrEnum):
    ROUTINE = "routine"
    ELEVATED = "elevated"
    URGENT = "urgent"


class ReportType(StrEnum):
    STAGNANT_WATER = "stagnant_water"
    FLOODING = "flooding"
    UNSAFE_WATER = "unsafe_water"
    ILLNESS_CLUSTER = "illness_cluster"
    WASTE_DUMPING = "waste_dumping"
    DUST_HAZE = "dust_haze"


class ReportSubmission(ServiceModel):
    district_id: str
    report_type: ReportType
    note: str = Field(min_length=1, max_length=1000)
    photo_reference: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class CommunityReport(ServiceModel):
    report_id: str
    district_id: str
    report_type: ReportType
    note: str
    photo_reference: str | None
    latitude: float | None
    longitude: float | None
    submitted_by: str
    submitted_on: date
    verification: VerificationStatus = VerificationStatus.PENDING
    verified_by: str | None = None
    verified_on: date | None = None
    priority: ReportPriority = ReportPriority.ROUTINE

    @property
    def counts_as_signal(self) -> bool:
        return self.verification is VerificationStatus.VERIFIED


class ReportVerification(ServiceModel):
    report_id: str
    status: VerificationStatus
    priority: ReportPriority = ReportPriority.ROUTINE


class ReportNotFound(LookupError):
    pass


class NotAVerifier(PermissionError):
    def __init__(self) -> None:
        super().__init__("Only a response coordinator can verify or reject a community report.")


class ReportsService:
    def __init__(
        self,
        reports: ReportStore,
        scope_guard: ScopeGuard,
        clock: Clock,
        events: EventPublisher | None = None,
    ) -> None:
        self._reports = reports
        self._scope_guard = scope_guard
        self._clock = clock
        self._events = events or NullEventPublisher()

    def submit(self, user: AuthenticatedUser, submission: ReportSubmission) -> CommunityReport:
        district = self._scope_guard.resolve_district(user, submission.district_id)
        report = self._reports.add(
            district_id=district.district_id,
            submission=submission,
            submitted_by=user.user_id,
            submitted_on=self._clock.today(),
        )
        self._events.publish(
            DomainEvent(
                event_type=EventType.REPORT_SUBMITTED,
                district_id=district.district_id,
                resource_id=report.report_id,
                summary=f"New {report.report_type.value} report in {district.name}",
                occurred_at=datetime.now(UTC),
            )
        )
        return report

    def list_reports(
        self,
        user: AuthenticatedUser,
        district_id: str | None = None,
        report_type: ReportType | None = None,
    ) -> tuple[CommunityReport, ...]:
        if district_id is not None:
            self._scope_guard.resolve_district(user, district_id)

        visible_ids = {
            district.district_id for district in self._scope_guard.visible_districts(user)
        }
        return tuple(
            report
            for report in self._reports.all_reports()
            if report.district_id in visible_ids
            and (district_id is None or report.district_id == district_id)
            and (report_type is None or report.report_type is report_type)
        )

    def verify(self, user: AuthenticatedUser, verification: ReportVerification) -> CommunityReport:
        """A coordinator confirms or rejects a report. Only then does it count."""
        if not user.coordinates_response:
            raise NotAVerifier()

        report = self._reports.find(verification.report_id)
        if report is None:
            raise ReportNotFound(f"Unknown report '{verification.report_id}'")
        self._scope_guard.resolve_district(user, report.district_id)

        return self._reports.set_verification(
            report_id=verification.report_id,
            status=verification.status,
            priority=verification.priority,
            verified_by=user.display_name,
            verified_on=self._clock.today(),
        )

    def find(self, user: AuthenticatedUser, report_id: str) -> CommunityReport:
        report = self._reports.find(report_id)
        if report is None:
            raise ReportNotFound(f"Unknown report '{report_id}'")
        if not user.scope.permits(report.district_id):
            raise DistrictAccessDenied(report.district_id)
        return report
