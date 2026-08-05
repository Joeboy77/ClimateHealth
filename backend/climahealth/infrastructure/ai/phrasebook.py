from climahealth.domain.models import HealthCondition, RiskLevel

CONDITION_PLAIN_NAMES: dict[HealthCondition, str] = {
    HealthCondition.MALARIA: "malaria",
    HealthCondition.CHOLERA: "cholera",
    HealthCondition.MENINGITIS: "meningitis",
    HealthCondition.DIARRHOEAL_DISEASE: "diarrhoea",
    HealthCondition.RESPIRATORY_HEAT_ILLNESS: "breathing problems and heat illness",
    HealthCondition.DENGUE: "dengue fever",
    HealthCondition.TYPHOID_FEVER: "typhoid fever",
    HealthCondition.SCHISTOSOMIASIS: "bilharzia",
    HealthCondition.LASSA_FEVER: "Lassa fever",
    HealthCondition.YELLOW_FEVER: "yellow fever",
    HealthCondition.LEPTOSPIROSIS: "leptospirosis",
    HealthCondition.TRACHOMA: "trachoma eye infection",
    HealthCondition.HEAT_STROKE: "heat stroke",
    HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY: "illness from polluted air",
    HealthCondition.CHILD_UNDERNUTRITION: "child undernutrition",
    HealthCondition.MATERNAL_HEAT_OUTCOMES: "heat harm in pregnancy",
}

LEVEL_PLAIN_WORDS: dict[RiskLevel, str] = {
    RiskLevel.LOW: "low",
    RiskLevel.MODERATE: "rising",
    RiskLevel.HIGH: "high",
    RiskLevel.SEVERE: "very high",
}

CITIZEN_ACTIONS: dict[HealthCondition, str] = {
    HealthCondition.MALARIA: (
        "Sleep under a treated net tonight and empty any standing water around your home."
    ),
    HealthCondition.CHOLERA: (
        "Drink only water you have boiled or treated, and wash your hands before eating."
    ),
    HealthCondition.MENINGITIS: (
        "Keep rooms ventilated, avoid crowded indoor spaces, and see a clinic quickly "
        "if someone has fever with a stiff neck."
    ),
    HealthCondition.DIARRHOEAL_DISEASE: (
        "Treat your drinking water and give oral rehydration salts early if a child has diarrhoea."
    ),
    HealthCondition.RESPIRATORY_HEAT_ILLNESS: (
        "Stay out of the midday sun, drink water often, and cover your nose when dust is heavy."
    ),
    HealthCondition.DENGUE: (
        "Cover or empty every water container around your home, and use repellent by day, "
        "because these mosquitoes bite in daylight."
    ),
    HealthCondition.TYPHOID_FEVER: (
        "Boil or treat drinking water, and wash your hands before preparing food."
    ),
    HealthCondition.SCHISTOSOMIASIS: (
        "Keep children out of slow-moving streams and ponds, and fetch water from a "
        "protected source."
    ),
    HealthCondition.LASSA_FEVER: (
        "Store food in sealed containers, block rat entry points, and never dry food on the ground."
    ),
    HealthCondition.YELLOW_FEVER: (
        "Check your family's yellow fever vaccination and clear standing water near the house."
    ),
    HealthCondition.LEPTOSPIROSIS: (
        "Stay out of flood water where you can, and cover any cut before wading."
    ),
    HealthCondition.TRACHOMA: ("Wash children's faces daily and keep flies away from their eyes."),
    HealthCondition.HEAT_STROKE: (
        "Rest in shade between midday and three, and drink water before you feel thirsty."
    ),
    HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY: (
        "Keep children and anyone with asthma or heart trouble indoors when the air is "
        "thick, and avoid burning refuse."
    ),
    HealthCondition.CHILD_UNDERNUTRITION: (
        "Take young children for growth monitoring, and ask the clinic about feeding "
        "support before the harvest gap bites."
    ),
    HealthCondition.MATERNAL_HEAT_OUTCOMES: (
        "If you are pregnant, avoid outdoor work between midday and three, drink water "
        "often, and go to the clinic if the baby's movements change."
    ),
}

OFFICER_ACTIONS: dict[HealthCondition, str] = {
    HealthCondition.MALARIA: (
        "Pre-position rapid diagnostic tests and artemisinin-based combination therapy, "
        "and brief community health volunteers on net use."
    ),
    HealthCondition.CHOLERA: (
        "Verify water quality at public standpipes, stage oral rehydration supplies, "
        "and put the district rapid response team on standby."
    ),
    HealthCondition.MENINGITIS: (
        "Confirm vaccine and ceftriaxone stock, alert clinicians to case definitions, "
        "and prepare lumbar puncture capacity."
    ),
    HealthCondition.DIARRHOEAL_DISEASE: (
        "Stock oral rehydration salts and zinc at every facility and inspect water points."
    ),
    HealthCondition.RESPIRATORY_HEAT_ILLNESS: (
        "Issue a heat and dust advisory and ensure clinics have salbutamol and oxygen."
    ),
    HealthCondition.DENGUE: (
        "Run container-clearing campaigns in dense settlements and brief clinicians to "
        "distinguish dengue from malaria on a negative RDT."
    ),
    HealthCondition.TYPHOID_FEVER: (
        "Test public water points, stock azithromycin, and trace cases to a shared source."
    ),
    HealthCondition.SCHISTOSOMIASIS: (
        "Schedule praziquantel mass administration in school-age children near affected "
        "water bodies."
    ),
    HealthCondition.LASSA_FEVER: (
        "Alert clinicians to viral haemorrhagic fever protocols, confirm ribavirin stock, "
        "and ready isolation and safe-burial capacity."
    ),
    HealthCondition.YELLOW_FEVER: (
        "Review vaccination coverage and prepare a reactive campaign if a case is confirmed."
    ),
    HealthCondition.LEPTOSPIROSIS: (
        "Warn flood-exposed workers, stock doxycycline, and brief clinicians on the "
        "fever-and-jaundice presentation."
    ),
    HealthCondition.TRACHOMA: (
        "Plan azithromycin distribution and reinforce face-washing and latrine messaging."
    ),
    HealthCondition.HEAT_STROKE: (
        "Issue a heat advisory, extend clinic hours, and prepare cooling and rehydration "
        "at facilities."
    ),
    HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY: (
        "Publish air quality readings, advise vulnerable groups to stay indoors, and "
        "enforce against open waste burning."
    ),
    HealthCondition.CHILD_UNDERNUTRITION: (
        "Pre-position therapeutic food, surge growth monitoring, and coordinate with "
        "agriculture on the harvest outlook."
    ),
    HealthCondition.MATERNAL_HEAT_OUTCOMES: (
        "Brief antenatal clinics on heat counselling and bring forward appointments "
        "for women in late pregnancy."
    ),
}

QUIET_HEADLINE = "No rising health risks for {district} today"
QUIET_SUMMARY = (
    "Conditions in {district} are calm right now. Nothing is building that needs action today."
)
QUIET_ACTION = "Keep doing the everyday basics: clean water, covered food, and a treated net."

RISK_HEADLINE = "{level_word} {condition} risk in {district}"
RISK_SUMMARY = (
    "Climate conditions in {district} point to a {level_word} chance of {condition} "
    "in the next {lag_phrase}. {driver} Those most at risk are {vulnerable_group_lowered}."
)

LAG_PHRASE_DAYS = "{minimum} to {maximum} days"
LAG_PHRASE_WEEKS = "{minimum} to {maximum} weeks"
LAG_PHRASE_UP_TO_DAYS = "the next {maximum} days"
LAG_PHRASE_MONTHS = "{minimum} to {maximum} months"
LAG_PHRASE_IMMEDIATE = "the next day or two"
