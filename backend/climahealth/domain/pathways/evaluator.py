from climahealth.domain.model.logistic import (
    ConditionModel,
    adjustment_for,
    describe_adjustment,
)
from climahealth.domain.models import (
    ClimateFeatures,
    Comparison,
    ContextMultiplier,
    DistrictContext,
    DomainModel,
    GateDefinition,
    PathwayDefinition,
    RiskAssessment,
    TriggerDefinition,
)
from climahealth.domain.scoring import (
    BASELINE_SIGNAL_COVERAGE,
    apply_multipliers,
    clamp_score,
    confidence_for,
    intensity_share,
    level_for_score,
    normalise_fired_weight,
    round_score,
)
from climahealth.domain.signals import describe_signal, describe_threshold, resolve_signal


class TriggerOutcome(DomainModel):
    fired: bool
    signal_available: bool
    weight: float
    earned_weight: float
    reason: str | None


def gate_allows(gate: GateDefinition, context: DistrictContext) -> bool:
    if context.season not in gate.permitted_seasons:
        return False
    if gate.requires_meningitis_belt and not context.in_meningitis_belt:
        return False
    return not (gate.requires_flood_prone and not context.flood_prone)


def comparison_holds(comparison: Comparison, value: float, threshold: float) -> bool:
    if comparison is Comparison.AT_LEAST:
        return value >= threshold
    return value <= threshold


def build_reason(trigger: TriggerDefinition, value: float) -> str:
    boundary = "at or above" if trigger.comparison is Comparison.AT_LEAST else "at or below"
    observed = describe_signal(trigger.signal, value)
    threshold = describe_threshold(trigger.signal, trigger.threshold)
    return f"{trigger.description} ({observed}, {boundary} the {threshold} threshold)"


def evaluate_trigger(
    trigger: TriggerDefinition,
    features: ClimateFeatures,
    context: DistrictContext,
) -> TriggerOutcome:
    value = resolve_signal(trigger.signal, features, context)
    if value is None:
        return TriggerOutcome(
            fired=False,
            signal_available=False,
            weight=trigger.weight,
            earned_weight=0.0,
            reason=None,
        )
    fired = comparison_holds(trigger.comparison, value, trigger.threshold)
    share = (
        intensity_share(
            value=value,
            threshold=trigger.threshold,
            saturation=trigger.saturation,
            at_least=trigger.comparison is Comparison.AT_LEAST,
        )
        if fired
        else 0.0
    )
    return TriggerOutcome(
        fired=fired,
        signal_available=True,
        weight=trigger.weight,
        earned_weight=trigger.weight * share,
        reason=build_reason(trigger, value) if fired else None,
    )


def applicable_multipliers(
    multipliers: tuple[ContextMultiplier, ...],
    context: DistrictContext,
) -> tuple[ContextMultiplier, ...]:
    return tuple(multiplier for multiplier in multipliers if context.holds(multiplier.condition))


def evaluate_pathway(
    pathway: PathwayDefinition,
    features: ClimateFeatures,
    context: DistrictContext,
    condition_model: ConditionModel | None = None,
) -> RiskAssessment | None:
    if not gate_allows(pathway.gate, context):
        return None

    outcomes = tuple(evaluate_trigger(trigger, features, context) for trigger in pathway.triggers)

    # Score against what could be measured. Counting an unreadable signal as
    # "did not fire" would quietly punish every pathway that depends on data we
    # do not hold, which is a claim about the world rather than about the data.
    measurable_weight = sum(outcome.weight for outcome in outcomes if outcome.signal_available)
    fired_weight = sum(outcome.earned_weight for outcome in outcomes)

    multipliers = applicable_multipliers(pathway.multipliers, context)
    score = apply_multipliers(
        normalise_fired_weight(fired_weight, measurable_weight),
        (multiplier.factor for multiplier in multipliers),
    )

    # The model only refines a decision the rules already made, and only above the
    # same signal-coverage floor that separates a threshold answer from a baseline
    # one. Below that floor there is too little to read for a learned model to add
    # anything honest. The adjustment is bounded either side, so the model can
    # nudge a score but never carry a pathway across a level boundary on its own.
    total_weight = sum(outcome.weight for outcome in outcomes)
    coverage = measurable_weight / total_weight if total_weight > 0 else 0.0
    model_applied = False
    model_reason: str | None = None

    if condition_model is not None and coverage >= BASELINE_SIGNAL_COVERAGE:
        probability = condition_model.probability_for(features, context)
        if probability is not None:
            adjustment = adjustment_for(probability)
            score = clamp_score(score + adjustment)
            model_applied = True
            model_reason = describe_adjustment(condition_model, adjustment)

    trigger_reasons = tuple(outcome.reason for outcome in outcomes if outcome.reason is not None)
    multiplier_reasons = tuple(multiplier.description for multiplier in multipliers)
    reasons = trigger_reasons + (multiplier_reasons if trigger_reasons else ())
    if model_reason is not None and trigger_reasons:
        reasons = (*reasons, model_reason)

    return RiskAssessment(
        condition=pathway.condition,
        level=level_for_score(score),
        score=round_score(score),
        lag_window=pathway.lag_window,
        vulnerable_group=pathway.vulnerable_group,
        reasons=reasons,
        confidence=confidence_for(
            measurable_weight=measurable_weight,
            total_weight=total_weight,
            model_applied=model_applied,
        ),
    )
