import json

import httpx
import pytest

from climahealth.infrastructure.ai.template_narrator import TemplateRiskNarrator
from climahealth.infrastructure.ai.translating_narrator import TranslatingRiskNarrator
from climahealth.infrastructure.ai.translators import (
    GHANA_NLP_ENDPOINT,
    GHANA_NLP_KEY_HEADER,
    CachingTranslator,
    GhanaNlpTranslator,
    NoTranslation,
)
from climahealth.services.narration import NarrationLanguage
from climahealth.services.ports import TranslationUnavailable
from tests.infrastructure.ai.test_narrators import request_for, risk

API_KEY = "test-subscription-key"


def translator_returning(payload: object, status_code: int = 200) -> GhanaNlpTranslator:
    def handler(request: httpx.Request) -> httpx.Response:
        if status_code != 200:
            return httpx.Response(status_code)
        return httpx.Response(200, json=payload)

    return GhanaNlpTranslator(API_KEY, httpx.Client(transport=httpx.MockTransport(handler)))


def test_english_needs_no_translator():
    assert NoTranslation().translate("Stay safe", NarrationLanguage.ENGLISH) == "Stay safe"


def test_no_translation_refuses_other_languages():
    with pytest.raises(TranslationUnavailable):
        NoTranslation().translate("Stay safe", NarrationLanguage.TWI)


def test_ghana_nlp_translates_to_twi():
    translated = translator_returning("Da ntoma ase anadwo yi").translate(
        "Sleep under a treated net tonight", NarrationLanguage.TWI
    )

    assert translated == "Da ntoma ase anadwo yi"


def test_ghana_nlp_sends_the_documented_request_shape():
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers.get(GHANA_NLP_KEY_HEADER)
        seen["body"] = json.loads(request.read())
        return httpx.Response(200, json="translated")

    GhanaNlpTranslator(API_KEY, httpx.Client(transport=httpx.MockTransport(handler))).translate(
        "Boil your water", NarrationLanguage.TWI
    )

    assert seen["url"] == GHANA_NLP_ENDPOINT
    assert seen["key"] == API_KEY
    assert seen["body"] == {"in": "Boil your water", "lang": "en-tw"}


@pytest.mark.parametrize(
    ("language", "expected_pair"),
    [
        (NarrationLanguage.TWI, "en-tw"),
        (NarrationLanguage.GA, "en-gaa"),
        (NarrationLanguage.EWE, "en-ee"),
        (NarrationLanguage.DAGBANI, "en-dag"),
    ],
)
def test_each_language_maps_to_its_pair_code(language, expected_pair):
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.read())
        return httpx.Response(200, json="ok")

    GhanaNlpTranslator(API_KEY, httpx.Client(transport=httpx.MockTransport(handler))).translate(
        "text", language
    )

    assert seen["body"]["lang"] == expected_pair


@pytest.mark.parametrize(
    "payload",
    [
        {"translated_text": "nsuo"},
        {"translation": "nsuo"},
        {"out": "nsuo"},
        {"result": "nsuo"},
        "nsuo",
    ],
)
def test_known_response_shapes_are_all_accepted(payload):
    assert translator_returning(payload).translate("water", NarrationLanguage.TWI) == "nsuo"


def test_an_unrecognised_response_shape_is_reported_as_unavailable():
    with pytest.raises(TranslationUnavailable):
        translator_returning({"unexpected": 42}).translate("water", NarrationLanguage.TWI)


def test_an_http_failure_is_reported_as_unavailable():
    with pytest.raises(TranslationUnavailable):
        translator_returning(None, status_code=503).translate("water", NarrationLanguage.TWI)


def test_a_rate_limited_response_is_reported_as_unavailable():
    with pytest.raises(TranslationUnavailable):
        translator_returning(None, status_code=429).translate("water", NarrationLanguage.TWI)


def test_repeated_phrases_are_translated_once():
    upstream = translator_returning("nsuo")
    caching = CachingTranslator(upstream)

    caching.translate("water", NarrationLanguage.TWI)
    caching.translate("water", NarrationLanguage.TWI)

    assert caching.upstream_calls == 1


def test_the_cache_separates_languages():
    caching = CachingTranslator(translator_returning("x"))

    caching.translate("water", NarrationLanguage.TWI)
    caching.translate("water", NarrationLanguage.GA)

    assert caching.upstream_calls == 2


def test_the_forecast_is_translated_when_a_language_is_requested():
    narrator = TranslatingRiskNarrator(
        TemplateRiskNarrator(), translator_returning("Twi text here")
    )

    narration = narrator.narrate(request_for(risk(), language=NarrationLanguage.TWI))

    assert narration.headline == "Twi text here"
    assert narration.summary == "Twi text here"
    assert narration.action_today == "Twi text here"
    assert narration.language is NarrationLanguage.TWI


def test_english_requests_never_call_the_translation_api():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("English must not be sent for translation")

    narrator = TranslatingRiskNarrator(
        TemplateRiskNarrator(),
        GhanaNlpTranslator(API_KEY, httpx.Client(transport=httpx.MockTransport(handler))),
    )

    narration = narrator.narrate(request_for(risk(), language=NarrationLanguage.ENGLISH))

    assert "malaria" in narration.headline.lower()


def test_a_failed_translation_falls_back_to_english_and_says_so():
    narrator = TranslatingRiskNarrator(
        TemplateRiskNarrator(), translator_returning(None, status_code=503)
    )

    narration = narrator.narrate(request_for(risk(), language=NarrationLanguage.TWI))

    assert "malaria" in narration.headline.lower()
    assert narration.language is NarrationLanguage.ENGLISH


def test_with_no_api_key_configured_the_forecast_still_works_in_english():
    narrator = TranslatingRiskNarrator(TemplateRiskNarrator(), NoTranslation())

    narration = narrator.narrate(request_for(risk(), language=NarrationLanguage.TWI))

    assert "malaria" in narration.headline.lower()
    assert narration.language is NarrationLanguage.ENGLISH


def test_translation_never_changes_the_underlying_risk():
    original = risk()
    request = request_for(original, language=NarrationLanguage.TWI)

    TranslatingRiskNarrator(TemplateRiskNarrator(), translator_returning("x")).narrate(request)

    assert request.risks == (original,)
    assert request.risks[0].score == 92.0
