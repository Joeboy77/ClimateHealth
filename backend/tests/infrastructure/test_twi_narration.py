from datetime import date

from climahealth.domain.models import (
    ConfidenceMode,
    HealthCondition,
    LagWindow,
    RiskAssessment,
    RiskLevel,
)
from climahealth.infrastructure.ai.template_narrator import TemplateRiskNarrator
from climahealth.infrastructure.ai.twi_narrator import TwiRiskNarrator
from climahealth.infrastructure.ai.twi_phrasebook import (
    TWI_CITIZEN_ACTIONS,
    TWI_CONDITION_NAMES,
)
from climahealth.services.narration import (
    NarrationLanguage,
    NarrationRequest,
    WordingProvenance,
)

TEST_DAY = date(2026, 8, 5)


def risk(condition: HealthCondition) -> RiskAssessment:
    return RiskAssessment(
        condition=condition,
        level=RiskLevel.SEVERE,
        score=90.0,
        lag_window=LagWindow(minimum_days=14, maximum_days=42),
        vulnerable_group="Children under five and pregnant women",
        reasons=("Heavy rainfall",),
        confidence=ConfidenceMode.THRESHOLD,
    )


def narrator() -> TwiRiskNarrator:
    return TwiRiskNarrator(TemplateRiskNarrator())


def request(condition: HealthCondition, language: NarrationLanguage) -> NarrationRequest:
    return NarrationRequest(district_name="Madina", risks=(risk(condition),), language=language)


def test_twi_is_composed_rather_than_translated():
    """Nothing English survives into the Twi, because it is built from Twi parts."""
    spoken = narrator().narrate(request(HealthCondition.MALARIA, NarrationLanguage.TWI))

    assert spoken.language is NarrationLanguage.TWI
    assert "atiridii" in spoken.headline.lower()
    assert "malaria" not in spoken.headline.lower()
    assert spoken.action_today == TWI_CITIZEN_ACTIONS[HealthCondition.MALARIA]


def test_twi_wording_declares_that_nobody_has_reviewed_it():
    """Unreviewed health advice must say so, rather than being taken on trust."""
    spoken = narrator().narrate(request(HealthCondition.MALARIA, NarrationLanguage.TWI))

    assert spoken.wording is WordingProvenance.CURATED_UNREVIEWED


def test_english_is_untouched():
    spoken = narrator().narrate(request(HealthCondition.MALARIA, NarrationLanguage.ENGLISH))

    assert spoken.language is NarrationLanguage.ENGLISH
    assert "malaria" in spoken.headline.lower()


def test_a_language_we_have_not_written_falls_through():
    spoken = narrator().narrate(request(HealthCondition.MALARIA, NarrationLanguage.GA))

    assert spoken.language is NarrationLanguage.ENGLISH


def test_every_condition_has_a_twi_name_and_a_twi_action():
    """A gap here would send somebody an English paragraph inside a Twi forecast."""
    for condition in HealthCondition:
        assert condition in TWI_CONDITION_NAMES, condition
        assert condition in TWI_CITIZEN_ACTIONS, condition


def test_the_twi_names_are_not_just_the_english_ones():
    borrowed = {
        HealthCondition.MENINGITIS,
        HealthCondition.SCHISTOSOMIASIS,
        HealthCondition.LEPTOSPIROSIS,
        HealthCondition.DENGUE,
        HealthCondition.TYPHOID_FEVER,
        HealthCondition.LASSA_FEVER,
    }
    translated = [
        condition
        for condition in HealthCondition
        if condition not in borrowed
        and TWI_CONDITION_NAMES[condition].lower() == condition.value.replace("_", " ")
    ]

    assert translated == []
