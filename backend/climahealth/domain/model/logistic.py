from math import exp

from climahealth.domain.models import (
    ClimateFeatures,
    DistrictContext,
    DomainModel,
    HealthCondition,
    SignalName,
)
from climahealth.domain.signals import resolve_signal

MODEL_ADJUSTMENT_LIMIT = 15.0
NEUTRAL_PROBABILITY = 0.5


class StandardisedTerm(DomainModel):
    """One learned coefficient, with the scaling it was trained under."""

    signal: SignalName
    mean: float
    scale: float
    coefficient: float

    def contribution(self, value: float) -> float:
        if self.scale == 0:
            return 0.0
        return self.coefficient * (value - self.mean) / self.scale


class ConditionModel(DomainModel):
    """A logistic model for one condition, trained offline and committed as data.

    Tier A of proposal section 6.3. It never decides on its own: the rules decide,
    and this adjusts the score within a bounded band when every signal the pathway
    needs was readable. Coefficients live in configuration for the same reason
    thresholds do, so what the engine believes can be read rather than guessed at.
    """

    condition: HealthCondition
    intercept: float
    terms: tuple[StandardisedTerm, ...]
    trained_on: str
    sample_count: int
    holdout_accuracy: float

    def probability_for(
        self,
        features: ClimateFeatures,
        context: DistrictContext,
    ) -> float | None:
        total = self.intercept
        for term in self.terms:
            value = resolve_signal(term.signal, features, context)
            if value is None:
                return None
            total += term.contribution(value)
        return 1.0 / (1.0 + exp(-max(min(total, 60.0), -60.0)))


def adjustment_for(probability: float) -> float:
    """Turn a probability into a bounded nudge around the threshold score."""
    return (probability - NEUTRAL_PROBABILITY) * 2 * MODEL_ADJUSTMENT_LIMIT


def describe_adjustment(condition_model: ConditionModel, adjustment: float) -> str:
    direction = "raises" if adjustment >= 0 else "lowers"
    return (
        f"The Tier A model {direction} this by {abs(adjustment):.1f} points "
        f"(trained on {condition_model.sample_count} {condition_model.trained_on} samples, "
        f"{condition_model.holdout_accuracy:.0%} holdout accuracy)"
    )
