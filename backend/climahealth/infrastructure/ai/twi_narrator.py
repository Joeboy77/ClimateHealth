from climahealth.domain.models import RiskAssessment
from climahealth.infrastructure.ai.twi_phrasebook import (
    TWI_CITIZEN_ACTIONS,
    TWI_CONDITION_NAMES,
    TWI_LEVEL_WORDS,
    TWI_ONSET_DAYS,
    TWI_ONSET_WEEKS,
    twi_group,
    twi_headline,
    twi_summary,
)
from climahealth.services.narration import (
    Narration,
    NarrationLanguage,
    NarrationRequest,
    WordingProvenance,
)
from climahealth.services.ports import RiskNarrator


def onset_phrase(risk: RiskAssessment) -> str:
    if risk.lag_window.maximum_days <= 14:
        return f"{risk.lag_window.minimum_days}-{risk.lag_window.maximum_days} {TWI_ONSET_DAYS}"
    return (
        f"{risk.lag_window.minimum_days // 7}-{risk.lag_window.maximum_days // 7} {TWI_ONSET_WEEKS}"
    )


class TwiRiskNarrator:
    """Composes the citizen forecast in Twi rather than translating it.

    A sentence built from Twi parts reads like Twi. The same sentence built in English and
    passed through a translator reads like English wearing Twi words, and for health
    advice that difference is the difference between being followed and being ignored.

    Anything without curated wording falls through to whatever narrator was given, so an
    unwritten condition gets the English rather than a guess.
    """

    def __init__(self, fallback: RiskNarrator) -> None:
        self._fallback = fallback

    def narrate(self, request: NarrationRequest) -> Narration:
        if request.language is not NarrationLanguage.TWI or not request.risks:
            return self._fallback.narrate(request)

        leading = request.risks[0]
        condition = TWI_CONDITION_NAMES.get(leading.condition)
        action = TWI_CITIZEN_ACTIONS.get(leading.condition)
        if condition is None or action is None:
            return self._fallback.narrate(request)

        return Narration(
            headline=twi_headline(condition, TWI_LEVEL_WORDS[leading.level], request.district_name),
            summary=twi_summary(
                condition,
                request.district_name,
                onset_phrase(leading),
                twi_group(leading.vulnerable_group),
            ),
            action_today=action,
            language=NarrationLanguage.TWI,
            wording=WordingProvenance.CURATED_UNREVIEWED,
        )
