import httpx

from climahealth.services.narration import NarrationLanguage
from climahealth.services.ports import TranslationUnavailable, Translator

GHANA_NLP_ENDPOINT = "https://translation-api.ghananlp.org/v1/translate"
GHANA_NLP_KEY_HEADER = "Ocp-Apim-Subscription-Key"
REQUEST_TIMEOUT_SECONDS = 8.0

GHANA_NLP_LANGUAGE_PAIRS: dict[NarrationLanguage, str] = {
    NarrationLanguage.TWI: "en-tw",
    NarrationLanguage.GA: "en-gaa",
    NarrationLanguage.EWE: "en-ee",
    NarrationLanguage.DAGBANI: "en-dag",
}


class NoTranslation:
    def translate(self, text: str, language: NarrationLanguage) -> str:
        if language is NarrationLanguage.ENGLISH:
            return text
        raise TranslationUnavailable(f"No translator configured for '{language.value}'")


class GhanaNlpTranslator:
    def __init__(
        self,
        api_key: str,
        http_client: httpx.Client,
        endpoint: str = GHANA_NLP_ENDPOINT,
    ) -> None:
        self._api_key = api_key
        self._http_client = http_client
        self._endpoint = endpoint

    def translate(self, text: str, language: NarrationLanguage) -> str:
        if language is NarrationLanguage.ENGLISH:
            return text

        pair = GHANA_NLP_LANGUAGE_PAIRS.get(language)
        if pair is None:
            raise TranslationUnavailable(f"Unsupported language '{language.value}'")

        try:
            response = self._http_client.post(
                self._endpoint,
                json={"in": text, "lang": pair},
                headers={GHANA_NLP_KEY_HEADER: self._api_key},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise TranslationUnavailable(f"Translation request failed: {error}") from error

        return self._extract(response.json())

    def _extract(self, payload: object) -> str:
        if isinstance(payload, str):
            return payload
        if isinstance(payload, dict):
            for field in ("translated_text", "translation", "out", "result"):
                value = payload.get(field)
                if isinstance(value, str) and value:
                    return value
        raise TranslationUnavailable("Translation response was not in a recognised shape")


class CachingTranslator:
    def __init__(self, upstream: Translator) -> None:
        self._upstream = upstream
        self._cache: dict[tuple[str, str], str] = {}
        self.upstream_calls = 0

    def translate(self, text: str, language: NarrationLanguage) -> str:
        key = (text, language.value)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        self.upstream_calls += 1
        translated = self._upstream.translate(text, language)
        self._cache[key] = translated
        return translated
