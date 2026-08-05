from datetime import date

import pytest

from climahealth.domain.models import ClimateFeatures, HealthCondition, RiskLevel, Season
from climahealth.infrastructure.climate.context_provider import (
    CalendarContextProvider,
    SeasonOverrideContextProvider,
)
from climahealth.infrastructure.climate.providers import DemoOverrideFeatureProvider
from climahealth.infrastructure.clock import FixedClock
from climahealth.infrastructure.seed.districts import MADINA, WA
from climahealth.services.demo_service import DemoConditionsRequest, DemoScenario, DemoService
from climahealth.services.models import District
from climahealth.services.risk_service import RiskService, highest_level

WET_SEASON_DAY = date(2026, 7, 27)
DRY_SEASON_DAY = date(2026, 1, 20)

CALM_FEATURES = ClimateFeatures(
    observed_on=WET_SEASON_DAY,
    rainfall_7d_mm=10.0,
    rainfall_14d_mm=20.0,
    consecutive_dry_days=3,
    humidity_mean_percent=60.0,
    temperature_mean_c=27.0,
    temperature_max_c=31.0,
    dust_concentration_ug_m3=8.0,
    particulate_matter_10_ug_m3=22.0,
)


class StubProvider:
    def __init__(self, features: ClimateFeatures = CALM_FEATURES) -> None:
        self.features = features

    def features_for(self, district: District) -> ClimateFeatures:
        return self.features


def build(day: date = WET_SEASON_DAY) -> tuple[RiskService, DemoService]:
    provider = DemoOverrideFeatureProvider(StubProvider())
    context_provider = SeasonOverrideContextProvider(CalendarContextProvider())
    clock = FixedClock(day)
    return (
        RiskService(provider=provider, context_provider=context_provider, clock=clock),
        DemoService(overrides=provider, seasons=context_provider, clock=clock),
    )


def conditions(district_id: str, scenario: DemoScenario) -> DemoConditionsRequest:
    return DemoConditionsRequest(district_id=district_id, scenario=scenario)


def test_report_carries_district_features_season_and_ranked_risks():
    risk_service, _ = build()

    report = risk_service.report_for(MADINA)

    assert report.district == MADINA
    assert report.season is Season.WET
    assert report.generated_on == WET_SEASON_DAY
    scores = [risk.score for risk in report.risks]
    assert scores == sorted(scores, reverse=True)


def test_overall_level_is_the_highest_of_the_ranked_risks():
    risk_service, demo_service = build()
    demo_service.set_conditions(MADINA, conditions("madina", DemoScenario.HEAVY_RAIN))

    report = risk_service.report_for(MADINA)

    assert report.overall_level in {RiskLevel.HIGH, RiskLevel.SEVERE}
    assert report.overall_level == report.risks[0].level


@pytest.mark.parametrize(
    ("levels", "expected"),
    [
        ((), RiskLevel.LOW),
        ((RiskLevel.LOW, RiskLevel.MODERATE), RiskLevel.MODERATE),
        ((RiskLevel.SEVERE, RiskLevel.LOW), RiskLevel.SEVERE),
        ((RiskLevel.HIGH, RiskLevel.MODERATE), RiskLevel.HIGH),
    ],
)
def test_highest_level_picks_the_most_severe(levels, expected):
    risk_service, _ = build()
    report = risk_service.report_for(MADINA)
    risks = tuple(report.risks[0].model_copy(update={"level": level}) for level in levels)

    assert highest_level(risks) == expected


def test_reports_for_many_districts_preserves_order():
    risk_service, _ = build()

    reports = risk_service.reports_for((MADINA, WA))

    assert [report.district.district_id for report in reports] == ["madina", "wa"]


def test_calendar_season_gates_meningitis_out_of_wa_in_july():
    risk_service, _ = build(day=WET_SEASON_DAY)

    report = risk_service.report_for(WA)

    assert HealthCondition.MENINGITIS not in {risk.condition for risk in report.risks}


def test_calendar_season_gates_meningitis_into_wa_in_january():
    risk_service, _ = build(day=DRY_SEASON_DAY)

    report = risk_service.report_for(WA)

    assert HealthCondition.MENINGITIS in {risk.condition for risk in report.risks}


def test_the_dry_and_dusty_scenario_forces_the_season_so_the_demo_works_in_july():
    risk_service, demo_service = build(day=WET_SEASON_DAY)

    demo_service.set_conditions(WA, conditions("wa", DemoScenario.DRY_AND_DUSTY))
    report = risk_service.report_for(WA)

    assert report.season is Season.DRY
    meningitis = next(risk for risk in report.risks if risk.condition is HealthCondition.MENINGITIS)
    assert meningitis.level in {RiskLevel.HIGH, RiskLevel.SEVERE}


def test_the_heavy_rain_scenario_forces_the_wet_season():
    risk_service, demo_service = build(day=DRY_SEASON_DAY)

    demo_service.set_conditions(MADINA, conditions("madina", DemoScenario.HEAVY_RAIN))

    assert risk_service.report_for(MADINA).season is Season.WET


def test_clearing_a_scenario_restores_the_calendar_season():
    risk_service, demo_service = build(day=WET_SEASON_DAY)
    demo_service.set_conditions(WA, conditions("wa", DemoScenario.DRY_AND_DUSTY))

    demo_service.clear_conditions(WA)

    assert risk_service.report_for(WA).season is Season.WET


def test_a_season_override_for_one_district_does_not_leak_to_another():
    risk_service, demo_service = build(day=WET_SEASON_DAY)

    demo_service.set_conditions(WA, conditions("wa", DemoScenario.DRY_AND_DUSTY))

    assert risk_service.report_for(MADINA).season is Season.WET


def test_clear_all_resets_every_override():
    risk_service, demo_service = build(day=WET_SEASON_DAY)
    demo_service.set_conditions(WA, conditions("wa", DemoScenario.DRY_AND_DUSTY))
    demo_service.set_conditions(MADINA, conditions("madina", DemoScenario.HEAVY_RAIN))

    demo_service.clear_all()

    assert risk_service.report_for(WA).season is Season.WET
    assert risk_service.report_for(MADINA).features.provenance.value == "live"


def test_an_explicit_season_beats_the_scenario_default():
    risk_service, demo_service = build(day=WET_SEASON_DAY)

    demo_service.set_conditions(
        WA,
        DemoConditionsRequest(
            district_id="wa", scenario=DemoScenario.HEAVY_RAIN, season=Season.DRY
        ),
    )

    assert risk_service.report_for(WA).season is Season.DRY
