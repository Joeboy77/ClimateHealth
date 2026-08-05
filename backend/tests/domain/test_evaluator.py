import pytest

from climahealth.domain.models import (
    Comparison,
    ContextCondition,
    ContextMultiplier,
    DistrictContext,
    GateDefinition,
    Season,
    SignalName,
    TriggerDefinition,
)
from climahealth.domain.pathways.evaluator import (
    applicable_multipliers,
    build_reason,
    comparison_holds,
    evaluate_trigger,
    gate_allows,
)
from tests.domain.conftest import climate_features


@pytest.mark.parametrize(
    ("comparison", "value", "threshold", "expected"),
    [
        (Comparison.AT_LEAST, 50.0, 50.0, True),
        (Comparison.AT_LEAST, 49.9, 50.0, False),
        (Comparison.AT_LEAST, 80.0, 50.0, True),
        (Comparison.AT_MOST, 30.0, 30.0, True),
        (Comparison.AT_MOST, 30.1, 30.0, False),
        (Comparison.AT_MOST, 10.0, 30.0, True),
    ],
)
def test_comparison_holds_at_boundaries(comparison, value, threshold, expected):
    assert comparison_holds(comparison, value, threshold) is expected


@pytest.mark.parametrize(
    ("gate", "season", "in_belt", "flood_prone", "expected"),
    [
        (GateDefinition(), Season.WET, False, False, True),
        (GateDefinition(), Season.DRY, False, False, True),
        (GateDefinition(permitted_seasons=(Season.DRY,)), Season.DRY, False, False, True),
        (GateDefinition(permitted_seasons=(Season.DRY,)), Season.WET, False, False, False),
        (GateDefinition(requires_meningitis_belt=True), Season.DRY, True, False, True),
        (GateDefinition(requires_meningitis_belt=True), Season.DRY, False, False, False),
        (GateDefinition(requires_flood_prone=True), Season.WET, False, True, True),
        (GateDefinition(requires_flood_prone=True), Season.WET, False, False, False),
        (
            GateDefinition(permitted_seasons=(Season.DRY,), requires_meningitis_belt=True),
            Season.WET,
            True,
            False,
            False,
        ),
    ],
)
def test_gate_allows(gate, season, in_belt, flood_prone, expected):
    context = DistrictContext(
        district_id="test",
        season=season,
        in_meningitis_belt=in_belt,
        flood_prone=flood_prone,
    )
    assert gate_allows(gate, context) is expected


RAINFALL_TRIGGER = TriggerDefinition(
    signal=SignalName.RAINFALL_7D_MM,
    comparison=Comparison.AT_LEAST,
    threshold=50.0,
    weight=3.0,
    description="Heavy rainfall in the past week creates mosquito breeding sites",
)

DUST_TRIGGER = TriggerDefinition(
    signal=SignalName.DUST_CONCENTRATION_UG_M3,
    comparison=Comparison.AT_LEAST,
    threshold=50.0,
    weight=3.0,
    description="Harmattan dust damages the lining of the throat and nose",
)


def test_trigger_fires_and_carries_a_reason(madina_context):
    outcome = evaluate_trigger(
        RAINFALL_TRIGGER, climate_features(rainfall_7d_mm=120.0), madina_context
    )

    assert outcome.fired is True
    assert outcome.signal_available is True
    assert "120 mm" in outcome.reason
    assert "50 mm" in outcome.reason


def test_trigger_that_does_not_fire_has_no_reason(madina_context):
    outcome = evaluate_trigger(
        RAINFALL_TRIGGER, climate_features(rainfall_7d_mm=10.0), madina_context
    )

    assert outcome.fired is False
    assert outcome.reason is None


def test_missing_signal_cannot_fire_and_is_flagged_unavailable(wa_context):
    outcome = evaluate_trigger(
        DUST_TRIGGER, climate_features(dust_concentration_ug_m3=None), wa_context
    )

    assert outcome.fired is False
    assert outcome.signal_available is False
    assert outcome.reason is None


def test_context_signal_is_resolved_from_district_not_climate(madina_context):
    stagnant_water_trigger = TriggerDefinition(
        signal=SignalName.STAGNANT_WATER_INDEX,
        comparison=Comparison.AT_LEAST,
        threshold=0.5,
        weight=2.0,
        description="Standing water is common in this district",
    )

    outcome = evaluate_trigger(stagnant_water_trigger, climate_features(), madina_context)

    assert outcome.fired is True


def test_build_reason_uses_direction_appropriate_wording():
    humidity_trigger = TriggerDefinition(
        signal=SignalName.HUMIDITY_MEAN_PERCENT,
        comparison=Comparison.AT_MOST,
        threshold=30.0,
        weight=3.0,
        description="Very dry air dries out the mucous barrier that blocks infection",
    )

    assert "at or below" in build_reason(humidity_trigger, 18.0)
    assert "at or above" in build_reason(RAINFALL_TRIGGER, 120.0)


FLOOD_MULTIPLIER = ContextMultiplier(
    condition=ContextCondition.FLOOD_PRONE,
    factor=1.15,
    description="District has a history of flooding",
)


def test_multiplier_applies_only_to_flood_prone_districts(madina_context, wa_context):
    assert applicable_multipliers((FLOOD_MULTIPLIER,), madina_context) == (FLOOD_MULTIPLIER,)
    assert applicable_multipliers((FLOOD_MULTIPLIER,), wa_context) == ()
