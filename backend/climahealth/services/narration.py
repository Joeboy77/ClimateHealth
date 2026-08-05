from enum import StrEnum

from climahealth.domain.models import RiskAssessment
from climahealth.services.models import ServiceModel


class NarrationLanguage(StrEnum):
    ENGLISH = "en"
    TWI = "tw"
    GA = "gaa"
    EWE = "ee"
    DAGBANI = "dag"


class WordingProvenance(StrEnum):
    """Where the words came from, which matters when they are health advice.

    Curated wording is written for the language rather than translated clause by clause.
    Until a native speaker has been through it, it is `curated_unreviewed`, and that
    travels out through the API so nobody has to remember it.
    """

    ENGLISH = "english"
    CURATED_REVIEWED = "curated_reviewed"
    CURATED_UNREVIEWED = "curated_unreviewed"
    MACHINE_TRANSLATED = "machine_translated"
    ENGLISH_FALLBACK = "english_fallback"


class NarrationAudience(StrEnum):
    CITIZEN = "citizen"
    OFFICER = "officer"


class NarrationRequest(ServiceModel):
    district_name: str
    risks: tuple[RiskAssessment, ...]
    audience: NarrationAudience = NarrationAudience.CITIZEN
    language: NarrationLanguage = NarrationLanguage.ENGLISH


class Narration(ServiceModel):
    headline: str
    summary: str
    action_today: str
    language: NarrationLanguage
    wording: WordingProvenance = WordingProvenance.ENGLISH
