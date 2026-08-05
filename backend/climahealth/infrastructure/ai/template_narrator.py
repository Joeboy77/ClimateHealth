from climahealth.domain.models import LagWindow, RiskAssessment, RiskLevel
from climahealth.infrastructure.ai.phrasebook import (
    CITIZEN_ACTIONS,
    CONDITION_PLAIN_NAMES,
    LAG_PHRASE_DAYS,
    LAG_PHRASE_IMMEDIATE,
    LAG_PHRASE_MONTHS,
    LAG_PHRASE_UP_TO_DAYS,
    LAG_PHRASE_WEEKS,
    LEVEL_PLAIN_WORDS,
    OFFICER_ACTIONS,
    QUIET_ACTION,
    QUIET_HEADLINE,
    QUIET_SUMMARY,
    RISK_HEADLINE,
    RISK_SUMMARY,
)
from climahealth.services.narration import (
    Narration,
    NarrationAudience,
    NarrationLanguage,
    NarrationRequest,
    WordingProvenance,
)

REPORTABLE_LEVELS = frozenset({RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.SEVERE})


DAYS_IN_WEEK = 7
DAYS_IN_MONTH = 30
WEEK_THRESHOLD_DAYS = 21
MONTH_THRESHOLD_DAYS = 90


def lag_phrase(lag_window: LagWindow) -> str:
    """Say days for fast pathways, weeks for slower ones, months for chronic."""
    minimum, maximum = lag_window.minimum_days, lag_window.maximum_days

    if maximum <= 3:
        return LAG_PHRASE_IMMEDIATE
    if maximum >= MONTH_THRESHOLD_DAYS:
        return LAG_PHRASE_MONTHS.format(
            minimum=max(minimum // DAYS_IN_MONTH, 1),
            maximum=maximum // DAYS_IN_MONTH,
        )
    if maximum > WEEK_THRESHOLD_DAYS:
        return LAG_PHRASE_WEEKS.format(
            minimum=max(minimum // DAYS_IN_WEEK, 1),
            maximum=maximum // DAYS_IN_WEEK,
        )
    if minimum == 0:
        return LAG_PHRASE_UP_TO_DAYS.format(maximum=maximum)
    return LAG_PHRASE_DAYS.format(minimum=minimum, maximum=maximum)


def leading_driver(risk: RiskAssessment) -> str:
    if not risk.reasons:
        return ""
    return f"{risk.reasons[0].split(' (')[0]}."


def english_provenance(requested: NarrationLanguage) -> WordingProvenance:
    """This narrator writes English and nothing else.

    Labelling English text with the language somebody asked for would be a lie the rest of
    the system then repeats, so an unmet request is reported as a fallback.
    """
    if requested is NarrationLanguage.ENGLISH:
        return WordingProvenance.ENGLISH
    return WordingProvenance.ENGLISH_FALLBACK


class TemplateRiskNarrator:
    def narrate(self, request: NarrationRequest) -> Narration:
        reportable = [risk for risk in request.risks if risk.level in REPORTABLE_LEVELS]
        if not reportable:
            return Narration(
                headline=QUIET_HEADLINE.format(district=request.district_name),
                summary=QUIET_SUMMARY.format(district=request.district_name),
                action_today=QUIET_ACTION,
                language=NarrationLanguage.ENGLISH,
                wording=english_provenance(request.language),
            )

        leading = reportable[0]
        condition = CONDITION_PLAIN_NAMES[leading.condition]
        level_word = LEVEL_PLAIN_WORDS[leading.level]
        actions = (
            OFFICER_ACTIONS if request.audience is NarrationAudience.OFFICER else CITIZEN_ACTIONS
        )

        return Narration(
            headline=RISK_HEADLINE.format(
                level_word=level_word.capitalize(),
                condition=condition,
                district=request.district_name,
            ),
            summary=RISK_SUMMARY.format(
                district=request.district_name,
                level_word=level_word,
                condition=condition,
                lag_phrase=lag_phrase(leading.lag_window),
                driver=leading_driver(leading),
                vulnerable_group_lowered=leading.vulnerable_group[0].lower()
                + leading.vulnerable_group[1:],
            ).replace("  ", " "),
            action_today=actions[leading.condition],
            language=NarrationLanguage.ENGLISH,
            wording=english_provenance(request.language),
        )
