from collections.abc import Sequence
from datetime import date, timedelta

from climahealth.services.models import ServiceModel
from climahealth.services.reports_service import CommunityReport, ReportType

CORROBORATION_WINDOW_DAYS = 14
FIRST_REPORT_WEIGHT = 0.30
PER_EXTRA_REPORT_WEIGHT = 0.15
MAXIMUM_COMMUNITY_VALUE = 0.85

REPORT_TYPE_TO_SIGNAL: dict[ReportType, str] = {
    ReportType.STAGNANT_WATER: "stagnant_water_index",
    ReportType.FLOODING: "stagnant_water_index",
    ReportType.UNSAFE_WATER: "unsafe_water_ratio",
    ReportType.WASTE_DUMPING: "poor_sanitation_index",
}


class CommunitySignal(ServiceModel):
    """A context value derived from verified reports rather than an instrument.

    Capped below certainty: corroborated citizen observation is strong evidence in
    a thinly instrumented district, but it is not a measurement.
    """

    signal: str
    value: float
    report_count: int
    report_types: tuple[ReportType, ...]
    newest_report_on: date


class CommunitySignals(ServiceModel):
    district_id: str
    signals: tuple[CommunitySignal, ...] = ()

    def value_for(self, signal: str) -> float | None:
        for entry in self.signals:
            if entry.signal == signal:
                return entry.value
        return None

    @property
    def contributing_report_count(self) -> int:
        return sum(entry.report_count for entry in self.signals)


def strength_from_count(count: int) -> float:
    """One report is suggestive; several corroborating reports are strong."""
    if count <= 0:
        return 0.0
    raw = FIRST_REPORT_WEIGHT + PER_EXTRA_REPORT_WEIGHT * (count - 1)
    return round(min(raw, MAXIMUM_COMMUNITY_VALUE), 2)


def derive_community_signals(
    district_id: str,
    reports: Sequence[CommunityReport],
    today: date,
) -> CommunitySignals:
    """Turn verified reports into context signals the engine can weigh.

    Only verified reports count, and only those inside the corroboration window,
    so a hazard cleared last month stops raising risk on its own.
    """
    cutoff = today - timedelta(days=CORROBORATION_WINDOW_DAYS)
    grouped: dict[str, list[CommunityReport]] = {}

    for report in reports:
        if report.district_id != district_id or not report.counts_as_signal:
            continue
        if report.submitted_on < cutoff:
            continue
        signal = REPORT_TYPE_TO_SIGNAL.get(report.report_type)
        if signal is None:
            continue
        grouped.setdefault(signal, []).append(report)

    signals = tuple(
        CommunitySignal(
            signal=signal,
            value=strength_from_count(len(entries)),
            report_count=len(entries),
            report_types=tuple(sorted({entry.report_type for entry in entries})),
            newest_report_on=max(entry.submitted_on for entry in entries),
        )
        for signal, entries in sorted(grouped.items())
    )

    return CommunitySignals(district_id=district_id, signals=signals)
