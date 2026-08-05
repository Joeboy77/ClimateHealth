import pytest

from climahealth.domain.models import ConfidenceMode, RiskLevel
from climahealth.domain.scoring import (
    apply_multipliers,
    clamp_score,
    confidence_for,
    level_for_score,
    normalise_fired_weight,
    round_score,
)


@pytest.mark.parametrize(
    ("fired_weight", "total_weight", "expected"),
    [
        (0.0, 10.0, 0.0),
        (5.0, 10.0, 50.0),
        (10.0, 10.0, 100.0),
        (2.5, 12.0, pytest.approx(20.833, abs=0.001)),
        (1.0, 0.0, 0.0),
    ],
)
def test_normalise_fired_weight(fired_weight, total_weight, expected):
    assert normalise_fired_weight(fired_weight, total_weight) == expected


@pytest.mark.parametrize(
    ("score", "factors", "expected"),
    [
        (50.0, (), 50.0),
        (50.0, (1.15,), pytest.approx(57.5)),
        (50.0, (1.1, 1.2), pytest.approx(66.0)),
        (95.0, (1.5,), 100.0),
        (-5.0, (), 0.0),
    ],
)
def test_apply_multipliers_clamps_to_valid_range(score, factors, expected):
    assert apply_multipliers(score, factors) == expected


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.0, RiskLevel.LOW),
        (24.9, RiskLevel.LOW),
        (25.0, RiskLevel.MODERATE),
        (49.9, RiskLevel.MODERATE),
        (50.0, RiskLevel.HIGH),
        (74.9, RiskLevel.HIGH),
        (75.0, RiskLevel.SEVERE),
        (100.0, RiskLevel.SEVERE),
    ],
)
def test_level_for_score_band_boundaries(score, expected):
    assert level_for_score(score) == expected


@pytest.mark.parametrize(
    ("measurable", "total", "model", "expected"),
    [
        (10.0, 10.0, False, ConfidenceMode.THRESHOLD),
        (6.0, 10.0, False, ConfidenceMode.THRESHOLD),
        (5.0, 10.0, False, ConfidenceMode.THRESHOLD),
        (4.0, 10.0, False, ConfidenceMode.BASELINE),
        (0.0, 10.0, False, ConfidenceMode.BASELINE),
        (0.0, 0.0, False, ConfidenceMode.BASELINE),
        (10.0, 10.0, True, ConfidenceMode.MODEL),
        (1.0, 10.0, True, ConfidenceMode.MODEL),
    ],
)
def test_confidence_reports_the_engine_tier(measurable, total, model, expected):
    assert confidence_for(measurable, total, model) == expected


@pytest.mark.parametrize(("score", "expected"), [(-1.0, 0.0), (101.0, 100.0), (42.0, 42.0)])
def test_clamp_score(score, expected):
    assert clamp_score(score) == expected


def test_round_score_is_stable_to_one_decimal():
    assert round_score(20.83333) == 20.8
