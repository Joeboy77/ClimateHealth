from datetime import date

from climahealth.domain.models import DistrictContext, Season
from climahealth.services.community_signals import (
    CommunitySignals,
    derive_community_signals,
)
from climahealth.services.models import District
from climahealth.services.ports import DistrictContextProvider, ReportStore


class CalendarContextProvider:
    def context_for(self, district: District, day: date) -> DistrictContext:
        return district.context_on(day)


class SeasonOverrideContextProvider:
    def __init__(self, upstream: DistrictContextProvider) -> None:
        self._upstream = upstream
        self._seasons: dict[str, Season] = {}

    def set_season(self, district_id: str, season: Season) -> None:
        self._seasons[district_id] = season

    def clear_season(self, district_id: str) -> None:
        self._seasons.pop(district_id, None)

    def clear_all_seasons(self) -> None:
        self._seasons.clear()

    def context_for(self, district: District, day: date) -> DistrictContext:
        context = self._upstream.context_for(district, day)
        overridden = self._seasons.get(district.district_id)
        if overridden is None:
            return context
        return context.model_copy(update={"season": overridden})


class CommunityReportContextProvider:
    """Fills unknown context signals from verified community reports.

    Proposal section 6.2: in a thinly instrumented district a verified citizen
    report is often the highest-resolution signal available. A measured value is
    never overwritten; reports only fill gaps.
    """

    def __init__(
        self,
        upstream: DistrictContextProvider,
        reports: ReportStore,
    ) -> None:
        self._upstream = upstream
        self._reports = reports

    def signals_for(self, district: District, day: date) -> CommunitySignals:
        return derive_community_signals(
            district.district_id, self._reports.for_district(district.district_id), day
        )

    def context_for(self, district: District, day: date) -> DistrictContext:
        context = self._upstream.context_for(district, day)
        signals = self.signals_for(district, day)
        if not signals.signals:
            return context

        updates = {
            signal.signal: signal.value
            for signal in signals.signals
            if getattr(context, signal.signal, None) is None
        }
        if not updates:
            return context
        return context.model_copy(update=updates)
