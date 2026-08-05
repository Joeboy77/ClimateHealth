from collections.abc import Iterable

from climahealth.domain.models import ConfidenceMode, RiskLevel

MINIMUM_SCORE = 0.0
MAXIMUM_SCORE = 100.0
SCORE_PRECISION = 1

RISK_LEVEL_UPPER_BOUNDS: tuple[tuple[float, RiskLevel], ...] = (
    (25.0, RiskLevel.LOW),
    (50.0, RiskLevel.MODERATE),
    (75.0, RiskLevel.HIGH),
)
HIGHEST_RISK_LEVEL = RiskLevel.SEVERE


def clamp_score(score: float) -> float:
    return min(max(score, MINIMUM_SCORE), MAXIMUM_SCORE)


def normalise_fired_weight(fired_weight: float, total_weight: float) -> float:
    if total_weight <= 0:
        return MINIMUM_SCORE
    return MAXIMUM_SCORE * fired_weight / total_weight


CREDIT_AT_THRESHOLD = 0.5


def intensity_share(
    value: float,
    threshold: float,
    saturation: float | None,
    at_least: bool,
) -> float:
    """How much of a fired trigger's weight the reading has earned.

    Crossing the published threshold earns half. The rest is earned across the
    span up to saturation, so two districts that both crossed the line are still
    told apart by how far past it they are.
    """
    if saturation is None:
        return 1.0
    span = saturation - threshold if at_least else threshold - saturation
    if span <= 0:
        return 1.0
    travelled = (value - threshold) / span if at_least else (threshold - value) / span
    return CREDIT_AT_THRESHOLD + (1 - CREDIT_AT_THRESHOLD) * min(max(travelled, 0.0), 1.0)


def apply_multipliers(score: float, factors: Iterable[float]) -> float:
    multiplied = score
    for factor in factors:
        multiplied *= factor
    return clamp_score(multiplied)


def round_score(score: float) -> float:
    return round(score, SCORE_PRECISION)


def level_for_score(score: float) -> RiskLevel:
    for upper_bound, level in RISK_LEVEL_UPPER_BOUNDS:
        if score < upper_bound:
            return level
    return HIGHEST_RISK_LEVEL


BASELINE_SIGNAL_COVERAGE = 0.5


def confidence_for(
    measurable_weight: float,
    total_weight: float,
    model_applied: bool = False,
) -> ConfidenceMode:
    """Tier A when a trained model contributed, Tier B on complete thresholds,
    Tier C when so little was readable that the answer is indicative only.
    """
    if model_applied:
        return ConfidenceMode.MODEL
    if total_weight <= 0:
        return ConfidenceMode.BASELINE
    coverage = measurable_weight / total_weight
    if coverage < BASELINE_SIGNAL_COVERAGE:
        return ConfidenceMode.BASELINE
    return ConfidenceMode.THRESHOLD
