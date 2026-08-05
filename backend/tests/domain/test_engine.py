import pytest

from climahealth.domain.engine import assess_district, rank_assessments
from climahealth.domain.model.logistic import MODEL_ADJUSTMENT_LIMIT
from climahealth.domain.model.trained import CONDITION_MODELS
from climahealth.domain.models import (
    ConfidenceMode,
    DistrictContext,
    FeatureProvenance,
    HealthCondition,
    RiskLevel,
    Season,
)
from tests.domain.conftest import climate_features


def assessment_for(assessments, condition):
    matches = [item for item in assessments if item.condition is condition]
    return matches[0] if matches else None


def test_madina_heavy_rain_puts_malaria_at_high_risk(madina_heavy_rain, madina_context):
    assessments = assess_district(madina_heavy_rain, madina_context)
    malaria = assessment_for(assessments, HealthCondition.MALARIA)

    assert malaria is not None
    assert malaria.level in (RiskLevel.HIGH, RiskLevel.SEVERE)
    assert malaria.score >= 50.0
    assert malaria.lag_window.minimum_days == 14
    assert malaria.lag_window.maximum_days == 42
    assert malaria.vulnerable_group == "Children under five and pregnant women"
    assert len(malaria.reasons) > 0


def test_wa_dust_puts_meningitis_at_high_risk(wa_dry_dusty, wa_context):
    assessments = assess_district(wa_dry_dusty, wa_context)
    meningitis = assessment_for(assessments, HealthCondition.MENINGITIS)

    assert meningitis is not None
    assert meningitis.level in (RiskLevel.HIGH, RiskLevel.SEVERE)
    assert meningitis.score >= 50.0
    top_scores = [item.score for item in assessments[:3]]
    assert meningitis.score >= min(top_scores)


def test_northern_dry_season_raises_several_dry_weather_conditions(wa_dry_dusty, wa_context):
    """Harmattan drives meningitis, Lassa fever and trachoma together, not one alone."""
    reported = {
        item.condition
        for item in assess_district(wa_dry_dusty, wa_context)
        if item.level in (RiskLevel.HIGH, RiskLevel.SEVERE)
    }

    assert HealthCondition.MENINGITIS in reported
    assert HealthCondition.LASSA_FEVER in reported
    assert len(reported) >= 3


def test_wet_and_dry_seasons_surface_different_conditions(
    madina_heavy_rain, madina_context, wa_dry_dusty, wa_context
):
    wet = {item.condition for item in assess_district(madina_heavy_rain, madina_context)}
    dry = {item.condition for item in assess_district(wa_dry_dusty, wa_context)}

    assert HealthCondition.LASSA_FEVER not in wet
    assert HealthCondition.TRACHOMA not in wet
    assert HealthCondition.LASSA_FEVER in dry


def test_malaria_falls_as_conditions_dry_out(madina_context):
    wet = climate_features(rainfall_7d_mm=120.0, rainfall_14d_mm=180.0, humidity_mean_percent=85.0)
    drying = climate_features(rainfall_7d_mm=40.0, rainfall_14d_mm=90.0, humidity_mean_percent=65.0)
    dry = climate_features(
        rainfall_7d_mm=0.0,
        rainfall_14d_mm=0.0,
        humidity_mean_percent=35.0,
        consecutive_dry_days=21,
    )

    scores = [
        assessment_for(assess_district(features, madina_context), HealthCondition.MALARIA).score
        for features in (wet, drying, dry)
    ]

    assert scores == sorted(scores, reverse=True)
    assert scores[0] > scores[-1]


def test_meningitis_is_gated_out_in_the_wet_season(wa_dry_dusty, madina_context):
    assessments = assess_district(wa_dry_dusty, madina_context)

    assert assessment_for(assessments, HealthCondition.MENINGITIS) is None


def test_meningitis_is_gated_out_outside_the_belt(wa_dry_dusty, wa_context):
    outside_belt = wa_context.model_copy(update={"in_meningitis_belt": False})

    assessments = assess_district(wa_dry_dusty, outside_belt)

    assert assessment_for(assessments, HealthCondition.MENINGITIS) is None


def test_ungated_pathways_are_always_reported_even_at_zero_score(madina_context):
    assessments = assess_district(climate_features(temperature_mean_c=15.0), madina_context)
    reported = {item.condition for item in assessments}

    assert HealthCondition.MALARIA in reported
    assert HealthCondition.CHOLERA in reported
    assert HealthCondition.RESPIRATORY_HEAT_ILLNESS in reported


def test_assessments_are_ranked_by_score_descending(wa_dry_dusty, wa_context):
    assessments = assess_district(wa_dry_dusty, wa_context)
    scores = [item.score for item in assessments]

    assert scores == sorted(scores, reverse=True)


def test_ranking_breaks_ties_alphabetically_for_determinism(madina_heavy_rain, madina_context):
    assessments = assess_district(madina_heavy_rain, madina_context)
    ranked = rank_assessments(assessments)

    keys = [(-item.score, item.condition.value) for item in ranked]
    assert keys == sorted(keys)


def test_engine_is_deterministic(madina_heavy_rain, madina_context):
    first = assess_district(madina_heavy_rain, madina_context)
    second = assess_district(madina_heavy_rain, madina_context)

    assert first == second


def test_missing_dust_data_lowers_the_engine_tier(wa_context):
    features = climate_features(
        consecutive_dry_days=40,
        humidity_mean_percent=18.0,
        temperature_max_c=39.0,
        dust_concentration_ug_m3=None,
    )

    meningitis = assessment_for(assess_district(features, wa_context), HealthCondition.MENINGITIS)

    assert meningitis.confidence in (ConfidenceMode.THRESHOLD, ConfidenceMode.BASELINE)


def test_a_condition_without_a_trained_model_never_reports_the_model_tier(
    madina_heavy_rain, madina_context
):
    assessments = assess_district(madina_heavy_rain, madina_context)
    unmodelled = [item for item in assessments if item.condition not in CONDITION_MODELS]

    assert unmodelled
    assert all(
        item.confidence in (ConfidenceMode.THRESHOLD, ConfidenceMode.BASELINE)
        for item in unmodelled
    )


def test_a_modelled_condition_reports_the_model_tier_above_the_coverage_floor(
    madina_heavy_rain, madina_context
):
    malaria = assessment_for(
        assess_district(madina_heavy_rain, madina_context), HealthCondition.MALARIA
    )

    assert malaria.confidence is ConfidenceMode.MODEL
    assert any("Tier A model" in reason for reason in malaria.reasons)


def test_the_model_cannot_move_a_score_beyond_its_bounded_band(madina_heavy_rain, madina_context):
    with_model = assessment_for(
        assess_district(madina_heavy_rain, madina_context), HealthCondition.MALARIA
    )
    without_model = assessment_for(
        assess_district(madina_heavy_rain, madina_context, models={}),
        HealthCondition.MALARIA,
    )

    assert without_model.confidence is not ConfidenceMode.MODEL
    assert abs(with_model.score - without_model.score) <= MODEL_ADJUSTMENT_LIMIT


def test_demo_provenance_does_not_change_the_engine_tier(madina_context):
    """Simulated readings are still evaluated by the threshold engine; provenance
    is reported separately so nothing is passed off as live."""
    live = climate_features(rainfall_7d_mm=120.0)
    demo = climate_features(rainfall_7d_mm=120.0, provenance=FeatureProvenance.DEMO)

    assert [item.confidence for item in assess_district(live, madina_context)] == [
        item.confidence for item in assess_district(demo, madina_context)
    ]


def test_flood_prone_multiplier_raises_cholera_score(madina_heavy_rain, madina_context):
    inland = madina_context.model_copy(update={"flood_prone": False})

    flood_prone_score = assessment_for(
        assess_district(madina_heavy_rain, madina_context), HealthCondition.CHOLERA
    ).score
    inland_score = assessment_for(
        assess_district(madina_heavy_rain, inland), HealthCondition.CHOLERA
    ).score

    assert flood_prone_score > inland_score


def test_multiplier_reason_is_reported_alongside_trigger_reasons(madina_heavy_rain, madina_context):
    cholera = assessment_for(
        assess_district(madina_heavy_rain, madina_context), HealthCondition.CHOLERA
    )

    assert "District has a history of flooding" in cholera.reasons


def test_a_pathway_with_no_fired_triggers_reports_no_reasons(madina_context):
    calm = climate_features(temperature_mean_c=15.0, temperature_max_c=20.0)

    respiratory = assessment_for(
        assess_district(calm, madina_context), HealthCondition.RESPIRATORY_HEAT_ILLNESS
    )

    assert respiratory.score == 0.0
    assert respiratory.level is RiskLevel.LOW
    assert respiratory.reasons == ()


def test_every_reported_assessment_carries_a_lag_window_and_vulnerable_group(
    wa_dry_dusty, wa_context
):
    assessments = assess_district(wa_dry_dusty, wa_context)

    assert assessments
    for item in assessments:
        assert item.lag_window.maximum_weeks >= item.lag_window.minimum_weeks
        assert item.vulnerable_group


@pytest.mark.parametrize("condition", list(HealthCondition))
def test_every_tier_one_condition_can_be_reported(
    condition, wa_dry_dusty, madina_heavy_rain, wa_context, madina_context
):
    reported = {
        item.condition
        for item in assess_district(wa_dry_dusty, wa_context)
        + assess_district(madina_heavy_rain, madina_context)
    }

    assert condition in reported


def test_an_unreadable_signal_does_not_drag_the_score_down(madina_context):
    """A pathway is judged on what could be measured, not punished for gaps."""
    complete = climate_features(rainfall_7d_mm=120.0, rainfall_14d_mm=180.0)
    with_gap = complete.model_copy(update={"dust_concentration_ug_m3": None})

    respiratory_complete = assessment_for(
        assess_district(complete, madina_context),
        HealthCondition.RESPIRATORY_HEAT_ILLNESS,
    )
    respiratory_with_gap = assessment_for(
        assess_district(with_gap, madina_context),
        HealthCondition.RESPIRATORY_HEAT_ILLNESS,
    )

    assert respiratory_with_gap.score >= respiratory_complete.score


def test_a_pathway_with_no_readable_signal_scores_zero(madina_context):
    blind = climate_features(dust_concentration_ug_m3=None, particulate_matter_10_ug_m3=None)
    context_without_water = madina_context.model_copy(
        update={
            "poor_sanitation_index": None,
            "unsafe_water_ratio": None,
            "stagnant_water_index": None,
        }
    )

    assessments = assess_district(blind, context_without_water)

    assert all(0 <= item.score <= 100 for item in assessments)


def test_a_coastal_district_carries_a_higher_cholera_risk_than_an_inland_one():
    """Proposal section 3.6: the sea changes what the same rainfall means."""
    features = climate_features(rainfall_7d_mm=140.0, rainfall_14d_mm=220.0)
    inland = DistrictContext(district_id="inland", season=Season.WET)
    coastal = DistrictContext(district_id="coastal", season=Season.WET, coastal=True)

    inland_cholera = assessment_for(assess_district(features, inland), HealthCondition.CHOLERA)
    coastal_cholera = assessment_for(assess_district(features, coastal), HealthCondition.CHOLERA)

    assert coastal_cholera.score > inland_cholera.score
    assert any("Coastal district" in reason for reason in coastal_cholera.reasons)


def test_coastal_standing_does_not_touch_a_pathway_the_sea_has_no_bearing_on():
    features = climate_features(dust_concentration_ug_m3=120.0, humidity_mean_percent=18.0)
    inland = DistrictContext(district_id="inland", season=Season.DRY, in_meningitis_belt=True)
    coastal = DistrictContext(
        district_id="coastal", season=Season.DRY, in_meningitis_belt=True, coastal=True
    )

    assert (
        assessment_for(assess_district(features, inland), HealthCondition.MENINGITIS).score
        == assessment_for(assess_district(features, coastal), HealthCondition.MENINGITIS).score
    )
