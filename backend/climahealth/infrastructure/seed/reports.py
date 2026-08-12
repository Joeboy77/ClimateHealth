from datetime import date

from climahealth.infrastructure.seed.incidents import ReportIdentifierSequence
from climahealth.services.reports_service import (
    CommunityReport,
    ReportPriority,
    ReportProgressEntry,
    ReportStage,
    ReportSubmission,
    ReportType,
    VerificationStatus,
)

SEEDED_REPORTS: tuple[CommunityReport, ...] = (
    CommunityReport(
        report_id="report-seed-1",
        district_id="madina",
        report_type=ReportType.STAGNANT_WATER,
        note="Large pool of standing water behind the market for over a week",
        photo_reference=None,
        latitude=5.6841,
        longitude=-0.1668,
        submitted_by="citizen-0417",
        submitted_on=date(2026, 7, 24),
        verification=VerificationStatus.VERIFIED,
        verified_by="Kwame Boateng",
        verified_on=date(2026, 7, 25),
        priority=ReportPriority.ELEVATED,
    ),
    CommunityReport(
        report_id="report-seed-2",
        district_id="madina",
        report_type=ReportType.WASTE_DUMPING,
        note="Refuse dumped into the storm drain near the school",
        photo_reference=None,
        latitude=5.6822,
        longitude=-0.1701,
        submitted_by="citizen-0982",
        submitted_on=date(2026, 7, 26),
        verification=VerificationStatus.VERIFIED,
        verified_by="Kwame Boateng",
        verified_on=date(2026, 7, 27),
        priority=ReportPriority.ROUTINE,
    ),
    CommunityReport(
        report_id="report-seed-3",
        district_id="wa",
        report_type=ReportType.DUST_HAZE,
        note="Very heavy dust for three days, many children coughing",
        photo_reference=None,
        latitude=10.0605,
        longitude=-2.5061,
        submitted_by="citizen-1120",
        submitted_on=date(2026, 7, 25),
    ),
)


class InMemoryReportStore:
    def __init__(self, reports: tuple[CommunityReport, ...] = SEEDED_REPORTS) -> None:
        self._reports = list(reports)
        self._identifiers = ReportIdentifierSequence()
        self._timeline: dict[str, list[ReportProgressEntry]] = {}

    def add(
        self,
        district_id: str,
        submission: ReportSubmission,
        submitted_by: str,
        submitted_on: date,
    ) -> CommunityReport:
        report = CommunityReport(
            report_id=self._identifiers.next_identifier(),
            district_id=district_id,
            report_type=submission.report_type,
            note=submission.note,
            photo_reference=submission.photo_reference,
            latitude=submission.latitude,
            longitude=submission.longitude,
            submitted_by=submitted_by,
            submitted_on=submitted_on,
        )
        self._reports.append(report)
        return report

    def all_reports(self) -> tuple[CommunityReport, ...]:
        return tuple(self._reports)

    def for_district(self, district_id: str) -> tuple[CommunityReport, ...]:
        return tuple(report for report in self._reports if report.district_id == district_id)

    def find(self, report_id: str) -> CommunityReport | None:
        return next((report for report in self._reports if report.report_id == report_id), None)

    def set_verification(
        self,
        report_id: str,
        status: VerificationStatus,
        priority: ReportPriority,
        verified_by: str,
        verified_on: date,
    ) -> CommunityReport:
        for index, report in enumerate(self._reports):
            if report.report_id != report_id:
                continue
            updated = report.model_copy(
                update={
                    "verification": status,
                    "priority": priority,
                    "verified_by": verified_by,
                    "verified_on": verified_on,
                }
            )
            self._reports[index] = updated
            return updated
        raise KeyError(report_id)

    def set_stage(
        self,
        report_id: str,
        stage: ReportStage,
        entry: ReportProgressEntry,
    ) -> CommunityReport:
        for index, report in enumerate(self._reports):
            if report.report_id != report_id:
                continue
            updated = report.model_copy(update={"stage": stage})
            self._reports[index] = updated
            self._timeline.setdefault(report_id, []).append(entry)
            return updated
        raise KeyError(report_id)

    def timeline_for(self, report_id: str) -> tuple[ReportProgressEntry, ...]:
        return tuple(self._timeline.get(report_id, ()))
