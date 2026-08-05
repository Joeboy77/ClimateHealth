from collections.abc import Mapping, Sequence

from climahealth.domain.model.logistic import ConditionModel
from climahealth.domain.model.trained import CONDITION_MODELS
from climahealth.domain.models import (
    ClimateFeatures,
    DistrictContext,
    HealthCondition,
    PathwayDefinition,
    RiskAssessment,
)
from climahealth.domain.pathways.definitions import ALL_PATHWAYS
from climahealth.domain.pathways.evaluator import evaluate_pathway


def rank_assessments(assessments: Sequence[RiskAssessment]) -> tuple[RiskAssessment, ...]:
    return tuple(sorted(assessments, key=lambda item: (-item.score, item.condition.value)))


def assess_district(
    features: ClimateFeatures,
    context: DistrictContext,
    pathways: Sequence[PathwayDefinition] = ALL_PATHWAYS,
    models: Mapping[HealthCondition, ConditionModel] = CONDITION_MODELS,
) -> tuple[RiskAssessment, ...]:
    assessments = [
        assessment
        for assessment in (
            evaluate_pathway(pathway, features, context, models.get(pathway.condition))
            for pathway in pathways
        )
        if assessment is not None
    ]
    return rank_assessments(assessments)
