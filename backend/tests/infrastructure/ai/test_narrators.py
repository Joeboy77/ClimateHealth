import pytest

from climahealth.domain.models import (
    ConfidenceMode,
    HealthCondition,
    LagWindow,
    RiskAssessment,
    RiskLevel,
)
from climahealth.infrastructure.ai.caching_narrator import (
    CachingRiskNarrator,
    FallbackRiskNarrator,
)
from climahealth.infrastructure.ai.template_narrator import TemplateRiskNarrator, lag_phrase
from climahealth.services.narration import (
    Narration,
    NarrationAudience,
    NarrationLanguage,
    NarrationRequest,
)


def risk(
    condition: HealthCondition = HealthCondition.MALARIA,
    level: RiskLevel = RiskLevel.SEVERE,
    score: float = 92.0,
    reasons: tuple[str, ...] = ("Heavy rainfall in the past week (7-day rainfall 120 mm)",),
) -> RiskAssessment:
    return RiskAssessment(
        condition=condition,
        level=level,
        score=score,
        lag_window=LagWindow(minimum_days=21, maximum_days=56),
        vulnerable_group="Children under five and pregnant women",
        reasons=reasons,
        confidence=ConfidenceMode.THRESHOLD,
    )


def request_for(*risks: RiskAssessment, **overrides: object) -> NarrationRequest:
    return NarrationRequest(district_name="Madina", risks=risks, **overrides)


class ExplodingNarrator:
    def narrate(self, request: NarrationRequest) -> Narration:
        raise RuntimeError("the language model is unreachable")


class CountingNarrator:
    def __init__(self) -> None:
        self.calls = 0

    def narrate(self, request: NarrationRequest) -> Narration:
        self.calls += 1
        return Narration(
            headline="counted",
            summary="counted",
            action_today="counted",
            language=request.language,
        )


def test_narration_names_the_condition_district_and_level():
    narration = TemplateRiskNarrator().narrate(request_for(risk()))

    assert "malaria" in narration.headline.lower()
    assert "Madina" in narration.summary
    assert "very high" in narration.headline.lower()


def test_narration_states_the_lag_window_and_vulnerable_group():
    narration = TemplateRiskNarrator().narrate(request_for(risk()))

    assert "3 to 8 weeks" in narration.summary
    assert "children under five" in narration.summary


def test_a_quiet_district_gets_reassurance_not_a_warning():
    narration = TemplateRiskNarrator().narrate(request_for(risk(level=RiskLevel.LOW)))

    assert "No rising health risks" in narration.headline
    assert "Madina" in narration.summary
    assert narration.action_today


def test_the_citizen_and_officer_actions_differ():
    citizen = TemplateRiskNarrator().narrate(request_for(risk()))
    officer = TemplateRiskNarrator().narrate(
        request_for(risk(), audience=NarrationAudience.OFFICER)
    )

    assert citizen.action_today != officer.action_today
    assert "net" in citizen.action_today.lower()
    assert "rapid diagnostic" in officer.action_today.lower()


@pytest.mark.parametrize("condition", list(HealthCondition))
def test_every_condition_has_citizen_and_officer_wording(condition):
    citizen = TemplateRiskNarrator().narrate(request_for(risk(condition=condition)))
    officer = TemplateRiskNarrator().narrate(
        request_for(risk(condition=condition), audience=NarrationAudience.OFFICER)
    )

    assert citizen.action_today
    assert officer.action_today
    assert citizen.headline


@pytest.mark.parametrize(
    ("minimum_days", "maximum_days", "expected"),
    [
        (2, 10, "2 to 10 days"),
        (3, 14, "3 to 14 days"),
        (5, 14, "5 to 14 days"),
        (0, 3, "the next day or two"),
        (14, 42, "2 to 6 weeks"),
        (7, 28, "1 to 4 weeks"),
        (0, 14, "the next 14 days"),
        (90, 365, "3 to 12 months"),
    ],
)
def test_lag_phrase_uses_days_for_fast_pathways(minimum_days, maximum_days, expected):
    """Cholera runs 2 to 10 days; saying "1 to 3 weeks" would overstate it."""
    assert lag_phrase(LagWindow(minimum_days=minimum_days, maximum_days=maximum_days)) == expected


def test_the_narrator_speaks_about_the_leading_risk_only():
    narration = TemplateRiskNarrator().narrate(
        request_for(
            risk(condition=HealthCondition.CHOLERA, score=90.0),
            risk(condition=HealthCondition.MALARIA, score=40.0, level=RiskLevel.MODERATE),
        )
    )

    assert "cholera" in narration.headline.lower()
    assert "malaria" not in narration.headline.lower()


def test_the_narrator_is_deterministic():
    narrator = TemplateRiskNarrator()
    request = request_for(risk())

    assert narrator.narrate(request) == narrator.narrate(request)


def test_the_narrator_never_alters_the_engine_decision():
    original = risk()
    request = request_for(original)

    TemplateRiskNarrator().narrate(request)

    assert request.risks == (original,)
    assert request.risks[0].level is RiskLevel.SEVERE
    assert request.risks[0].score == 92.0
    assert request.risks[0].confidence is ConfidenceMode.THRESHOLD


def test_narration_carries_the_requested_language_through():
    narration = TemplateRiskNarrator().narrate(
        request_for(risk(), language=NarrationLanguage.ENGLISH)
    )

    assert narration.language is NarrationLanguage.ENGLISH


def test_caching_narrator_calls_upstream_once_per_distinct_request():
    upstream = CountingNarrator()
    narrator = CachingRiskNarrator(upstream)
    request = request_for(risk())

    narrator.narrate(request)
    narrator.narrate(request)

    assert upstream.calls == 1


def test_caching_narrator_treats_a_different_level_as_a_different_entry():
    upstream = CountingNarrator()
    narrator = CachingRiskNarrator(upstream)

    narrator.narrate(request_for(risk(level=RiskLevel.SEVERE)))
    narrator.narrate(request_for(risk(level=RiskLevel.MODERATE)))

    assert upstream.calls == 2


def test_caching_narrator_separates_citizen_and_officer_text():
    upstream = CountingNarrator()
    narrator = CachingRiskNarrator(upstream)

    narrator.narrate(request_for(risk()))
    narrator.narrate(request_for(risk(), audience=NarrationAudience.OFFICER))

    assert upstream.calls == 2


def test_priming_the_cache_avoids_a_later_upstream_call():
    upstream = CountingNarrator()
    narrator = CachingRiskNarrator(upstream)
    request = request_for(risk())

    narrator.prime(request)
    narrator.narrate(request)

    assert upstream.calls == 1


def test_a_failing_language_model_falls_back_to_templates():
    narrator = FallbackRiskNarrator(ExplodingNarrator(), TemplateRiskNarrator())

    narration = narrator.narrate(request_for(risk()))

    assert "malaria" in narration.headline.lower()
