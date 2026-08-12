from datetime import date

from sqlalchemy import func, select

from climahealth.infrastructure.database.engine import SessionFactory
from climahealth.infrastructure.database.tables import CommunityReportRow, ReportProgressRow
from climahealth.services.reports_service import (
    STAGE_LABELS,
    CommunityReport,
    ReportPriority,
    ReportProgressEntry,
    ReportStage,
    ReportSubmission,
    ReportType,
    VerificationStatus,
)


def _to_report(row: CommunityReportRow) -> CommunityReport:
    return CommunityReport(
        report_id=row.report_id,
        district_id=row.district_id,
        report_type=ReportType(row.report_type),
        note=row.note,
        photo_reference=row.photo_reference,
        latitude=row.latitude,
        longitude=row.longitude,
        submitted_by=row.submitted_by,
        submitted_on=row.submitted_on,
        verification=VerificationStatus(row.verification),
        verified_by=row.verified_by,
        verified_on=row.verified_on,
        priority=ReportPriority(row.priority),
        stage=ReportStage(row.stage),
    )


class PostgresReportStore:
    def __init__(self, sessions: SessionFactory) -> None:
        self._sessions = sessions

    def seed(self, reports: tuple[CommunityReport, ...]) -> None:
        with self._sessions.begin() as session:
            existing = set(session.scalars(select(CommunityReportRow.report_id)))
            for report in reports:
                if report.report_id in existing:
                    continue
                session.add(
                    CommunityReportRow(
                        report_id=report.report_id,
                        district_id=report.district_id,
                        report_type=report.report_type.value,
                        note=report.note,
                        photo_reference=report.photo_reference,
                        latitude=report.latitude,
                        longitude=report.longitude,
                        submitted_by=report.submitted_by,
                        submitted_on=report.submitted_on,
                        verification=report.verification.value,
                        verified_by=report.verified_by,
                        verified_on=report.verified_on,
                        priority=report.priority.value,
                        stage=report.stage.value,
                    )
                )

    def add(
        self,
        district_id: str,
        submission: ReportSubmission,
        submitted_by: str,
        submitted_on: date,
    ) -> CommunityReport:
        with self._sessions.begin() as session:
            next_number = (
                session.scalar(select(func.count()).select_from(CommunityReportRow)) or 0
            ) + 1
            report_id = f"report-{next_number}"
            while session.get(CommunityReportRow, report_id) is not None:
                next_number += 1
                report_id = f"report-{next_number}"
            row = CommunityReportRow(
                report_id=report_id,
                district_id=district_id,
                report_type=submission.report_type.value,
                note=submission.note,
                photo_reference=submission.photo_reference,
                latitude=submission.latitude,
                longitude=submission.longitude,
                submitted_by=submitted_by,
                submitted_on=submitted_on,
            )
            session.add(row)
            session.flush()
            return _to_report(row)

    def all_reports(self) -> tuple[CommunityReport, ...]:
        with self._sessions.begin() as session:
            rows = session.scalars(
                select(CommunityReportRow).order_by(CommunityReportRow.submitted_on.desc())
            ).all()
            return tuple(_to_report(row) for row in rows)

    def for_district(self, district_id: str) -> tuple[CommunityReport, ...]:
        with self._sessions.begin() as session:
            rows = session.scalars(
                select(CommunityReportRow).where(CommunityReportRow.district_id == district_id)
            ).all()
            return tuple(_to_report(row) for row in rows)

    def find(self, report_id: str) -> CommunityReport | None:
        with self._sessions.begin() as session:
            row = session.get(CommunityReportRow, report_id)
            return _to_report(row) if row else None

    def set_verification(
        self,
        report_id: str,
        status: VerificationStatus,
        priority: ReportPriority,
        verified_by: str,
        verified_on: date,
    ) -> CommunityReport:
        with self._sessions.begin() as session:
            row = session.get(CommunityReportRow, report_id)
            if row is None:
                raise KeyError(report_id)
            row.verification = status.value
            row.priority = priority.value
            row.verified_by = verified_by
            row.verified_on = verified_on
            session.flush()
            return _to_report(row)

    def set_stage(
        self,
        report_id: str,
        stage: ReportStage,
        entry: ReportProgressEntry,
    ) -> CommunityReport:
        with self._sessions.begin() as session:
            row = session.get(CommunityReportRow, report_id)
            if row is None:
                raise KeyError(report_id)
            row.stage = stage.value
            session.add(
                ReportProgressRow(
                    report_id=report_id,
                    stage=entry.stage.value,
                    note=entry.note,
                    actor_name=entry.actor_name,
                    actor_role=entry.actor_role,
                    recorded_at=entry.recorded_at,
                )
            )
            session.flush()
            return _to_report(row)

    def timeline_for(self, report_id: str) -> tuple[ReportProgressEntry, ...]:
        with self._sessions.begin() as session:
            rows = session.scalars(
                select(ReportProgressRow)
                .where(ReportProgressRow.report_id == report_id)
                .order_by(ReportProgressRow.entry_id)
            ).all()
            return tuple(
                ReportProgressEntry(
                    stage=ReportStage(row.stage),
                    stage_label=STAGE_LABELS[ReportStage(row.stage)],
                    note=row.note,
                    actor_name=row.actor_name,
                    actor_role=row.actor_role,
                    recorded_at=row.recorded_at,
                )
                for row in rows
            )
