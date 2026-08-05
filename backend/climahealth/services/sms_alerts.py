from datetime import date
from enum import StrEnum

from pydantic import Field

from climahealth.domain.models import HealthCondition, RiskLevel
from climahealth.services.models import ServiceModel
from climahealth.services.narration import NarrationLanguage
from climahealth.services.risk_service import DistrictRiskReport

GSM7_SINGLE_SEGMENT = 160
GSM7_CONCATENATED_SEGMENT = 153
UCS2_SINGLE_SEGMENT = 70
UCS2_CONCATENATED_SEGMENT = 67
SENDABLE_LEVELS: frozenset[RiskLevel] = frozenset({RiskLevel.HIGH, RiskLevel.SEVERE})

GSM7_BASIC = (
    "@\u00a3$\u00a5\u00e8\u00e9\u00f9\u00ec\u00f2\u00c7\n\u00d8\u00f8\r\u00c5\u00e5"
    "\u0394_\u03a6\u0393\u039b\u03a9\u03a0\u03a8\u03a3\u0398\u039e\u00c6\u00e6\u00df\u00c9"
    " !\"#\u00a4%&'()*+,-./0123456789:;<=>?"
    "\u00a1ABCDEFGHIJKLMNOPQRSTUVWXYZ\u00c4\u00d6\u00d1\u00dc\u00a7"
    "\u00bfabcdefghijklmnopqrstuvwxyz\u00e4\u00f6\u00f1\u00fc\u00e0"
)
GSM7_EXTENDED = "^{}\\[~]|\u20ac"


class SmsEncoding(StrEnum):
    """How the network will encode this text, which decides what a segment costs.

    A single non-GSM character, such as the Twi \u0254, moves the whole message to
    UCS-2 and cuts a segment from 160 characters to 70. On a national broadcast
    that is the difference between one message and three.
    """

    GSM7 = "gsm7"
    UCS2 = "ucs2"


def encoding_for(text: str) -> SmsEncoding:
    if all(character in GSM7_BASIC or character in GSM7_EXTENDED for character in text):
        return SmsEncoding.GSM7
    return SmsEncoding.UCS2


def billable_length(text: str) -> int:
    """Extended GSM characters occupy two positions, so length is not len()."""
    if encoding_for(text) is SmsEncoding.UCS2:
        return len(text)
    return sum(2 if character in GSM7_EXTENDED else 1 for character in text)


CONDITION_WORDS: dict[NarrationLanguage, dict[HealthCondition, str]] = {
    NarrationLanguage.ENGLISH: {
        HealthCondition.MALARIA: "malaria",
        HealthCondition.CHOLERA: "cholera",
        HealthCondition.MENINGITIS: "meningitis",
        HealthCondition.DIARRHOEAL_DISEASE: "diarrhoea",
        HealthCondition.RESPIRATORY_HEAT_ILLNESS: "breathing illness",
        HealthCondition.DENGUE: "dengue",
        HealthCondition.TYPHOID_FEVER: "typhoid",
        HealthCondition.SCHISTOSOMIASIS: "bilharzia",
        HealthCondition.LASSA_FEVER: "Lassa fever",
        HealthCondition.YELLOW_FEVER: "yellow fever",
        HealthCondition.LEPTOSPIROSIS: "leptospirosis",
        HealthCondition.TRACHOMA: "eye infection",
        HealthCondition.HEAT_STROKE: "heat stroke",
        HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY: "air pollution illness",
        HealthCondition.CHILD_UNDERNUTRITION: "child hunger",
        HealthCondition.MATERNAL_HEAT_OUTCOMES: "heat harm in pregnancy",
    },
    NarrationLanguage.TWI: {
        HealthCondition.MALARIA: "atiridii",
        HealthCondition.CHOLERA: "kolera",
        HealthCondition.MENINGITIS: "meningitis",
        HealthCondition.DIARRHOEAL_DISEASE: "ayamtuo",
        HealthCondition.RESPIRATORY_HEAT_ILLNESS: "ahome yare",
    },
}

ACTION_WORDS: dict[NarrationLanguage, dict[HealthCondition, str]] = {
    NarrationLanguage.ENGLISH: {
        HealthCondition.MALARIA: "Sleep under a treated net. Empty standing water.",
        HealthCondition.CHOLERA: "Boil or treat drinking water. Wash hands with soap.",
        HealthCondition.MENINGITIS: "Cover nose in dust. Go to clinic for stiff neck or fever.",
        HealthCondition.DIARRHOEAL_DISEASE: "Treat drinking water. Use ORS for diarrhoea.",
        HealthCondition.RESPIRATORY_HEAT_ILLNESS: "Stay indoors midday. Keep inhalers close.",
        HealthCondition.DENGUE: "Empty water containers. Cover them.",
        HealthCondition.TYPHOID_FEVER: "Boil drinking water. Wash hands before eating.",
        HealthCondition.SCHISTOSOMIASIS: "Avoid swimming or wading in still water.",
        HealthCondition.LASSA_FEVER: "Store grain in covered containers. Keep rats out.",
        HealthCondition.YELLOW_FEVER: "Check your vaccination. Avoid mosquito bites.",
        HealthCondition.LEPTOSPIROSIS: "Do not wade in flood water. Cover any wound.",
        HealthCondition.TRACHOMA: "Wash children's faces daily. Keep flies off.",
        HealthCondition.HEAT_STROKE: "Drink water often. Rest in shade at midday.",
        HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY: "Avoid smoke. Do not burn waste.",
        HealthCondition.CHILD_UNDERNUTRITION: "Take under-fives for growth checks at the clinic.",
        HealthCondition.MATERNAL_HEAT_OUTCOMES: "Pregnant women: rest in shade, drink water often.",
    },
    NarrationLanguage.TWI: {
        HealthCondition.MALARIA: "Da ntoma ase. Hwie nsuo a agyina no gu.",
        HealthCondition.CHOLERA: "Noa wo nsuo ansa na woanom. Hohoro wo nsa.",
    },
}

SENTENCE_TEMPLATES: dict[NarrationLanguage, str] = {
    NarrationLanguage.ENGLISH: (
        "{level} {condition} risk in {district} in {onset}. {action} -ClimaHealth"
    ),
    NarrationLanguage.TWI: (
        "{level} {condition} wo {district} wo {onset} mu. {action} -ClimaHealth"
    ),
}

LEVEL_WORDS: dict[NarrationLanguage, dict[RiskLevel, str]] = {
    NarrationLanguage.ENGLISH: {RiskLevel.HIGH: "High", RiskLevel.SEVERE: "SEVERE"},
    NarrationLanguage.TWI: {RiskLevel.HIGH: "Kese", RiskLevel.SEVERE: "KESE PAA"},
}


class SmsAlert(ServiceModel):
    """One district's warning, sized for a phone that cannot open an app."""

    district_id: str
    district_name: str
    language: NarrationLanguage
    condition: HealthCondition
    level: RiskLevel
    body: str
    character_count: int = Field(ge=0)
    encoding: SmsEncoding
    segments: int = Field(ge=1)
    generated_on: date

    @property
    def fits_one_segment(self) -> bool:
        return self.segments == 1


class SmsDelivery(ServiceModel):
    recipient: str
    reference: str
    accepted: bool
    provider_code: str
    provider_message: str


class SenderIdStatus(ServiceModel):
    """Whether the configured sender name is cleared to send.

    Checked before a broadcast rather than discovered by one: an unapproved
    sender is rejected by the network, and finding that out mid-demonstration is
    the wrong moment.
    """

    sender_id: str
    approval: str
    whitelisted: bool
    known: bool

    @property
    def can_send(self) -> bool:
        return self.approval.lower() == "approved"


class SmsDispatchResult(ServiceModel):
    district_id: str
    sent: bool
    preview_only: bool
    deliveries: tuple[SmsDelivery, ...]


def segments_for(text: str) -> int:
    encoding = encoding_for(text)
    single, concatenated = (
        (GSM7_SINGLE_SEGMENT, GSM7_CONCATENATED_SEGMENT)
        if encoding is SmsEncoding.GSM7
        else (UCS2_SINGLE_SEGMENT, UCS2_CONCATENATED_SEGMENT)
    )
    length = billable_length(text)
    if length <= single:
        return 1
    return -(-length // concatenated)


def word_for(
    table: dict[NarrationLanguage, dict[HealthCondition, str]],
    language: NarrationLanguage,
    condition: HealthCondition,
) -> str:
    localised = table.get(language, {})
    if condition in localised:
        return localised[condition]
    return table[NarrationLanguage.ENGLISH][condition]


def level_word(language: NarrationLanguage, level: RiskLevel) -> str:
    return LEVEL_WORDS.get(language, LEVEL_WORDS[NarrationLanguage.ENGLISH])[level]


def onset_phrase(minimum_days: int, maximum_days: int) -> str:
    """Say it the way a person would, not the way the model stores it."""
    if maximum_days <= 14:
        return f"{minimum_days}-{maximum_days} days"
    minimum_weeks = minimum_days // 7
    maximum_weeks = maximum_days // 7
    if minimum_weeks == 0:
        return f"under {maximum_weeks} weeks"
    if minimum_weeks == maximum_weeks:
        return f"about {maximum_weeks} weeks"
    return f"{minimum_weeks}-{maximum_weeks} weeks"


def compose_alert(
    report: DistrictRiskReport,
    language: NarrationLanguage = NarrationLanguage.ENGLISH,
) -> SmsAlert | None:
    """Build the single message that matters for this district, or nothing.

    One risk, one action, no link. A message that needs a second segment costs
    twice as much to send to every household, so the leading risk is the whole
    message and the rest of the ranking stays in the app.
    """
    raised = [risk for risk in report.risks if risk.level in SENDABLE_LEVELS]
    if not raised:
        return None

    leading = max(raised, key=lambda risk: risk.score)
    condition = word_for(CONDITION_WORDS, language, leading.condition)
    action = word_for(ACTION_WORDS, language, leading.condition)
    onset = onset_phrase(leading.lag_window.minimum_days, leading.lag_window.maximum_days)

    body = SENTENCE_TEMPLATES.get(language, SENTENCE_TEMPLATES[NarrationLanguage.ENGLISH]).format(
        level=level_word(language, leading.level),
        condition=condition,
        district=report.district.name,
        onset=onset,
        action=action,
    )

    return SmsAlert(
        district_id=report.district.district_id,
        district_name=report.district.name,
        language=language,
        condition=leading.condition,
        level=leading.level,
        body=body,
        character_count=billable_length(body),
        encoding=encoding_for(body),
        segments=segments_for(body),
        generated_on=report.generated_on,
    )
