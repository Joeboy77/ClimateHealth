from climahealth.services.narration import (
    Narration,
    NarrationLanguage,
    NarrationRequest,
    WordingProvenance,
)
from climahealth.services.ports import RiskNarrator, TranslationUnavailable, Translator


class TranslatingRiskNarrator:
    def __init__(self, base: RiskNarrator, translator: Translator) -> None:
        self._base = base
        self._translator = translator

    def narrate(self, request: NarrationRequest) -> Narration:
        english = self._base.narrate(
            request.model_copy(update={"language": NarrationLanguage.ENGLISH})
        )
        if request.language is NarrationLanguage.ENGLISH:
            return english

        try:
            return Narration(
                headline=self._translator.translate(english.headline, request.language),
                summary=self._translator.translate(english.summary, request.language),
                action_today=self._translator.translate(english.action_today, request.language),
                language=request.language,
                wording=WordingProvenance.MACHINE_TRANSLATED,
            )
        except TranslationUnavailable:
            # English somebody can read beats a language they asked for and did not get,
            # but the response must admit that is what happened.
            return english.model_copy(update={"wording": WordingProvenance.ENGLISH_FALLBACK})
