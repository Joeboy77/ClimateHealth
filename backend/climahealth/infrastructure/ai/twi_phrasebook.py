"""Curated Twi for the citizen-facing wording.

Two things make this different from running the English through a translator.

First, it is composed in Twi rather than translated sentence by sentence. Health advice
put through machine translation clause by clause produces text that is grammatical and
still wrong, and "empty standing water" coming back as something about emptying a
container of drinking water is the kind of error nobody notices until it matters.

Second, the orthography here is the real one, with ɔ and ɛ. That is right for a screen
and wrong for SMS: a single non-GSM character moves the whole message to UCS-2 and cuts a
segment from 160 characters to 70. `services/sms_alerts.py` therefore keeps its own
transliterated Twi that stays inside GSM-7, and the two are deliberately not shared.

**None of this has been reviewed by a native speaker.** It is written to be understood
rather than to be elegant, and every entry is marked unreviewed until somebody who speaks
Twi has been through it. `WordingProvenance` carries that fact out through the API so it
cannot quietly be forgotten.
"""

from climahealth.domain.models import HealthCondition, RiskLevel

TWI_CONDITION_NAMES: dict[HealthCondition, str] = {
    HealthCondition.MALARIA: "atiridii",
    HealthCondition.CHOLERA: "kolera",
    HealthCondition.MENINGITIS: "meningitis (kɔn mu yareɛ)",
    HealthCondition.DIARRHOEAL_DISEASE: "ayamtuo",
    HealthCondition.RESPIRATORY_HEAT_ILLNESS: "ahome yareɛ ne ɔhyew yareɛ",
    HealthCondition.DENGUE: "dengue atiridii",
    HealthCondition.TYPHOID_FEVER: "typhoid atiridii",
    HealthCondition.SCHISTOSOMIASIS: "bilharzia",
    HealthCondition.LASSA_FEVER: "Lassa atiridii",
    HealthCondition.YELLOW_FEVER: "atiridii kɔkɔɔ",
    HealthCondition.LEPTOSPIROSIS: "leptospirosis",
    HealthCondition.TRACHOMA: "aniwa yareɛ",
    HealthCondition.HEAT_STROKE: "ɔhyew yareɛ",
    HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY: "mframa fĩ yareɛ",
    HealthCondition.CHILD_UNDERNUTRITION: "mmofra aduanepa hia",
    HealthCondition.MATERNAL_HEAT_OUTCOMES: "ɔhyew haw wɔ nyinsɛn mu",
}

TWI_LEVEL_WORDS: dict[RiskLevel, str] = {
    RiskLevel.LOW: "kakra",
    RiskLevel.MODERATE: "ɛreforo",
    RiskLevel.HIGH: "kɛseɛ",
    RiskLevel.SEVERE: "kɛseɛ paa",
}

TWI_CITIZEN_ACTIONS: dict[HealthCondition, str] = {
    HealthCondition.MALARIA: (
        "Da ntontom ntoma ase anadwo yi, na hwie nsuo biara a agyina wɔ wo fie ho no gu."
    ),
    HealthCondition.CHOLERA: (
        "Nom nsuo a woanoa anaa woayɛ ho adwuma nkoaa, na hohoro wo nsa ansa na woadidi."
    ),
    HealthCondition.MENINGITIS: (
        "Ma mframa nkɔ adan mu, twe wo ho firi nnipadɔm ho, na kɔ ayaresabea ntɛm sɛ "
        "obi kɔn mu yɛ den na ɔwɔ atiridii a."
    ),
    HealthCondition.DIARRHOEAL_DISEASE: (
        "Yɛ wo nsuo ho adwuma ansa na woanom, na fa ORS ma abofra ntɛm sɛ ɔwɔ ayamtuo a."
    ),
    HealthCondition.RESPIRATORY_HEAT_ILLNESS: (
        "Twe wo ho firi owia mu awia, nom nsuo pii, na kata wo hwene sɛ mfuturo dɔɔso a."
    ),
    HealthCondition.DENGUE: (
        "Kata anaa hwie nsuo a ɛwɔ wo fie ho nyinaa gu, ɛfiri sɛ ntontom yi ka awia."
    ),
    HealthCondition.TYPHOID_FEVER: (
        "Noa wo nsuo ansa na woanom, na hohoro wo nsa ansa na woanoa aduane."
    ),
    HealthCondition.SCHISTOSOMIASIS: (
        "Mma mmofra nnware wɔ nsuo a ɛnnene mu, na sa nsuo firi baabi a ɛho teɛ."
    ),
    HealthCondition.LASSA_FEVER: (
        "Fa wo aduane sie adaka a ano ato mu, na pam akusie mfiri wo fie."
    ),
    HealthCondition.YELLOW_FEVER: (
        "Hwɛ sɛ woanya aduru a ɛbɔ ho ban, na bɔ wo ho ban firi ntontom nkeka ho."
    ),
    HealthCondition.LEPTOSPIROSIS: ("Nnantew nsuoyiri mu, na kata akuro biara a ɛwɔ wo ho so."),
    HealthCondition.TRACHOMA: ("Hohoro mmofra anim da biara, na pam nwansena mfiri wɔn anim."),
    HealthCondition.HEAT_STROKE: ("Nom nsuo mpɛn pii, na home wɔ nwunu ase awia."),
    HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY: (
        "Twe wo ho firi wisie ho, na nhye nwira anaa mfee."
    ),
    HealthCondition.CHILD_UNDERNUTRITION: (
        "Fa mmofra a wɔnnii mfeɛ enum kɔ ayaresabea ma wɔnhwɛ wɔn nkɔsoɔ."
    ),
    HealthCondition.MATERNAL_HEAT_OUTCOMES: (
        "Mmaa a wɔnyinsɛn: home wɔ nwunu ase, na nom nsuo mpɛn pii."
    ),
}

TWI_ONSET_DAYS = "nna"
TWI_ONSET_WEEKS = "nnawɔtwe"


def twi_headline(condition: str, level: str, district: str) -> str:
    """ "Atiridii kɛseɛ paa wɔ Madina" — the verdict first, as in the English."""
    return f"{condition.capitalize()} {level} wɔ {district}"


def twi_summary(condition: str, district: str, onset: str, group: str) -> str:
    return (
        f"Ewiem tebea a ɛwɔ {district} kyerɛ sɛ {condition} bɛtumi aba wɔ {onset} mu. "
        f"Wɔn a asiane no kɔ wɔn so paa ne {group}."
    )


TWI_VULNERABLE_GROUPS: dict[str, str] = {
    "Children under five and pregnant women": "mmofra nkumaa ne mmaa a wɔnyinsɛn",
    "Children under five": "mmofra a wɔnnii mfeɛ enum",
    "Children under five and densely settled low-sanitation communities": (
        "mmofra nkumaa ne mpɔtam a ahoteɛ sua"
    ),
    "Children and young adults under thirty": "mmofra ne mmabunu",
    "Older adults, young children and people with asthma": (
        "mpanyimfoɔ, mmofra nkumaa ne wɔn a wɔwɔ ahome yareɛ"
    ),
    "Children who swim, fish or fetch water": ("mmofra a wɔdware, yi nsuomnam anaa wɔsa nsuo"),
    "Pregnant women, especially those working outdoors": (
        "mmaa a wɔnyinsɛn, titire wɔn a wɔyɛ adwuma abɔnten"
    ),
}


def twi_group(english: str) -> str:
    """Falls back to the English phrase rather than guessing at one we have not written."""
    return TWI_VULNERABLE_GROUPS.get(english, english)
