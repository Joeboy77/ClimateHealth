from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import Field

from climahealth.services.access import AuthenticatedUser, DistrictAccessDenied, UserRole
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


class ReportStage(StrEnum):
    """How far along fixing the thing is, which is a different question from whether
    the report was true. Authenticity is decided once, by somebody who went and looked;
    progress keeps moving after that.
    """

    SUBMITTED = "submitted"
    VALIDATED = "validated"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


ORDERED_STAGES: tuple[ReportStage, ...] = (
    ReportStage.SUBMITTED,
    ReportStage.VALIDATED,
    ReportStage.IN_PROGRESS,
    ReportStage.RESOLVED,
)

STAGE_LABELS: dict[ReportStage, str] = {
    ReportStage.SUBMITTED: "Submitted",
    ReportStage.VALIDATED: "Validated on the ground",
    ReportStage.IN_PROGRESS: "Being worked on",
    ReportStage.RESOLVED: "Resolved",
    ReportStage.REJECTED: "Could not be confirmed",
}

ALLOWED_TRANSITIONS: dict[ReportStage, tuple[ReportStage, ...]] = {
    ReportStage.SUBMITTED: (ReportStage.VALIDATED, ReportStage.REJECTED),
    ReportStage.VALIDATED: (ReportStage.IN_PROGRESS, ReportStage.REJECTED),
    ReportStage.IN_PROGRESS: (ReportStage.RESOLVED,),
    ReportStage.RESOLVED: (),
    ReportStage.REJECTED: (),
}


def progress_percent(stage: ReportStage) -> int:
    """A rejected report is finished, not 25 per cent done, so it reads as complete."""
    if stage is ReportStage.REJECTED:
        return 100
    return round((ORDERED_STAGES.index(stage) + 1) / len(ORDERED_STAGES) * 100)


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
    stage: ReportStage = ReportStage.SUBMITTED

    @property
    def photo_url(self) -> str | None:
        """Cloudinary hands back a URL; the local store hands back a filename that this
        API serves. Clients should not have to know which one they are looking at."""
        if self.photo_reference is None:
            return None
        if self.photo_reference.startswith("http"):
            return self.photo_reference
        return f"/reports/photo/{self.photo_reference}"

    @property
    def counts_as_signal(self) -> bool:
        return self.verification is VerificationStatus.VERIFIED


class ReportVerification(ServiceModel):
    report_id: str
    status: VerificationStatus
    priority: ReportPriority = ReportPriority.ROUTINE


class ReportProgressEntry(ServiceModel):
    """One step in a report's life. Append-only: entries are never edited or removed,
    because the point of a timeline is that it cannot be quietly rewritten."""

    stage: ReportStage
    stage_label: str
    note: str | None
    actor_name: str
    actor_role: str
    recorded_at: datetime


class ReportProgress(ServiceModel):
    report_id: str
    stage: ReportStage
    stage_label: str
    percent: int
    next_stages: tuple[ReportStage, ...]
    timeline: tuple[ReportProgressEntry, ...]


class StageAdvance(ServiceModel):
    stage: ReportStage
    note: str | None = Field(default=None, max_length=500)


class InvalidStageChange(ValueError):
    pass


class NotAValidator(PermissionError):
    def __init__(self) -> None:
        super().__init__(
            "Only an Ɔhwɛfoɔ who has been to the site, or a coordinator, may validate a report."
        )


class NotAResponder(PermissionError):
    def __init__(self) -> None:
        super().__init__("Only an agency responder or a coordinator may move work forward.")


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

    def advance_stage(
        self, user: AuthenticatedUser, report_id: str, advance: StageAdvance
    ) -> ReportProgress:
        """Move a report one step, and write down who moved it.

        Validation and repair are different jobs held by different people. An Ɔhwɛfoɔ
        decides whether the thing is real, because they went and stood there; an agency
        decides when the work has started and finished, because they are doing it.
        Neither can do the other's step.
        """
        report = self._reports.find(report_id)
        if report is None:
            raise ReportNotFound(f"Unknown report '{report_id}'")
        self._scope_guard.resolve_district(user, report.district_id)

        permitted = ALLOWED_TRANSITIONS[report.stage]
        if advance.stage not in permitted:
            raise InvalidStageChange(
                f"A report that is {STAGE_LABELS[report.stage].lower()} cannot become "
                f"{STAGE_LABELS[advance.stage].lower()}."
            )

        if advance.stage in (ReportStage.VALIDATED, ReportStage.REJECTED):
            if not user.validates_in_the_field:
                raise NotAValidator()
        elif not (user.coordinates_response or user.role is UserRole.RESPONDER):
            raise NotAResponder()

        entry = ReportProgressEntry(
            stage=advance.stage,
            stage_label=STAGE_LABELS[advance.stage],
            note=advance.note,
            actor_name=user.display_name,
            actor_role=user.role_name,
            recorded_at=self._clock.now(),
        )
        updated = self._reports.set_stage(report_id, advance.stage, entry)

        # Authenticity is decided once, by whoever went and looked, and the rest of the
        # platform already keys points and community signals off that judgement.
        if advance.stage is ReportStage.VALIDATED:
            self._reports.set_verification(
                report_id=report_id,
                status=VerificationStatus.VERIFIED,
                priority=report.priority,
                verified_by=user.display_name,
                verified_on=self._clock.today(),
            )
        elif advance.stage is ReportStage.REJECTED:
            self._reports.set_verification(
                report_id=report_id,
                status=VerificationStatus.REJECTED,
                priority=report.priority,
                verified_by=user.display_name,
                verified_on=self._clock.today(),
            )

        self._events.publish(
            DomainEvent(
                event_type=EventType.REPORT_SUBMITTED,
                district_id=report.district_id,
                resource_id=report_id,
                summary=f"Report {report_id} is now {STAGE_LABELS[advance.stage].lower()}",
                occurred_at=datetime.now(UTC),
            )
        )
        return self.progress_for(user, report_id, updated)

    def progress_for(
        self,
        user: AuthenticatedUser,
        report_id: str,
        report: CommunityReport | None = None,
    ) -> ReportProgress:
        resolved = report if report is not None else self._reports.find(report_id)
        if resolved is None:
            raise ReportNotFound(f"Unknown report '{report_id}'")
        if not user.scope.permits(resolved.district_id):
            raise DistrictAccessDenied(resolved.district_id)

        return ReportProgress(
            report_id=resolved.report_id,
            stage=resolved.stage,
            stage_label=STAGE_LABELS[resolved.stage],
            percent=progress_percent(resolved.stage),
            next_stages=ALLOWED_TRANSITIONS[resolved.stage],
            timeline=self._reports.timeline_for(resolved.report_id),
        )

    def find(self, user: AuthenticatedUser, report_id: str) -> CommunityReport:
        report = self._reports.find(report_id)
        if report is None:
            raise ReportNotFound(f"Unknown report '{report_id}'")
        if not user.scope.permits(report.district_id):
            raise DistrictAccessDenied(report.district_id)
        return report
