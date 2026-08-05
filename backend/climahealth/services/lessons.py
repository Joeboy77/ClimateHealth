from climahealth.domain.models import HealthCondition
from climahealth.services.citizens import GuardianTier
from climahealth.services.models import ServiceModel


class Lesson(ServiceModel):
    """One short teaching, pitched at one age band.

    Proposal section 11.1: the lesson is triggered by the weather, so it arrives on the
    day it matters rather than sitting in a library nobody opens. Section 11.4 is why the
    same hazard is written four ways: a nine-year-old and a grandmother both need to know
    about standing water, and neither is served by the other's version.
    """

    condition: HealthCondition
    tier: GuardianTier
    title: str
    body: str
    action: str
    read_seconds: int


CHILD_VOICE = GuardianTier.ANANSI
TEEN_VOICE = GuardianTier.RISK_SCOUT
ADULT_VOICE = GuardianTier.COMMUNITY_CHAMPION
ELDER_VOICE = GuardianTier.VOICE_FIRST

# Roughly 180 words a minute, floored so nothing claims to take zero time.
WORDS_PER_MINUTE = 180


def reading_seconds(text: str) -> int:
    return max(15, round(len(text.split()) / WORDS_PER_MINUTE * 60))


def lesson(
    condition: HealthCondition,
    tier: GuardianTier,
    title: str,
    body: str,
    action: str,
) -> Lesson:
    return Lesson(
        condition=condition,
        tier=tier,
        title=title,
        body=body,
        action=action,
        read_seconds=reading_seconds(body),
    )


LESSONS: tuple[Lesson, ...] = (
    # Malaria
    lesson(
        HealthCondition.MALARIA,
        CHILD_VOICE,
        "Where the mosquito hides",
        "Anansi looked for the mosquito everywhere. Not in the tall grass. Not under the "
        "roof. He found her in a bucket of old rain, laying her eggs on the water like "
        "tiny boats. Mosquitoes cannot grow up without still water. Tip the water away "
        "and the eggs go with it.",
        "Find one thing outside holding old rain, and pour it out.",
    ),
    lesson(
        HealthCondition.MALARIA,
        TEEN_VOICE,
        "Why rain today means fever in three weeks",
        "A mosquito needs still water for about ten days to go from egg to adult. Then "
        "the parasite needs another week or two inside her before she can pass it on. "
        "That is the gap between the rain and the fever, and it is why a warning now is "
        "worth more than a clinic visit later.",
        "Walk your compound and count every container holding water. That number is your risk.",
    ),
    lesson(
        HealthCondition.MALARIA,
        ADULT_VOICE,
        "The window between the rain and the cases",
        "Heavy rain leaves standing water, and standing water becomes mosquitoes in about "
        "ten days. Cases follow two to six weeks after the rain. Clearing containers this "
        "week removes the breeding sites before that generation ever hatches, which is "
        "cheaper and surer than treating the fevers.",
        "Empty and turn over containers, and sleep under a treated net tonight.",
    ),
    lesson(
        HealthCondition.MALARIA,
        ELDER_VOICE,
        "After the rain, check the water",
        "Mosquitoes breed in water that sits still. After heavy rain there is more of it, "
        "and more mosquitoes follow within a few weeks. Older people and small children "
        "suffer the worst of the fever.",
        "Sleep under a treated net, and ask someone to empty any water sitting near your home.",
    ),
    # Cholera
    lesson(
        HealthCondition.CHOLERA,
        CHILD_VOICE,
        "The water that looks clean",
        "Some water looks clean and still carries something that makes you very sick. You "
        "cannot see it, smell it or taste it. Boiling the water kills it. So does washing "
        "your hands with soap before you eat.",
        "Wash your hands with soap before every meal today.",
    ),
    lesson(
        HealthCondition.CHOLERA,
        TEEN_VOICE,
        "Why cholera moves so fast",
        "Cholera can take somebody from healthy to dangerously dehydrated in a day, which "
        "is far quicker than malaria. It spreads when flood water reaches drinking water. "
        "That is why a flood warning is also a water warning, and why the response has to "
        "start before anybody is ill.",
        "Make sure your household is boiling or treating drinking water from today.",
    ),
    lesson(
        HealthCondition.CHOLERA,
        ADULT_VOICE,
        "Flooding is a drinking-water problem",
        "When drains overflow, waste reaches wells and standpipes. Cholera then appears in "
        "two to ten days, far faster than most climate-driven illness, and it kills "
        "through dehydration rather than infection alone. Oral rehydration salts kept at "
        "home save lives in the hours before a clinic.",
        "Boil or treat all drinking water, and keep rehydration salts at home.",
    ),
    lesson(
        HealthCondition.CHOLERA,
        ELDER_VOICE,
        "Boil the water this week",
        "Flooding has reached the water people drink. Illness from it comes quickly, "
        "within days, and it takes fluid from the body fast.",
        "Boil drinking water. If anyone has watery stools, give rehydration salts and go "
        "to the clinic the same day.",
    ),
    # Meningitis
    lesson(
        HealthCondition.MENINGITIS,
        CHILD_VOICE,
        "The dusty wind",
        "In the dry season a dusty wind blows down from the north. The dust dries the "
        "inside of your nose, and a dry nose cannot catch germs the way a wet one does. "
        "That is how the germ gets in.",
        "Cover your nose with a cloth when the dust is thick outside.",
    ),
    lesson(
        HealthCondition.MENINGITIS,
        TEEN_VOICE,
        "Why the belt exists",
        "Meningitis outbreaks follow a band across Africa where the Harmattan is driest. "
        "Dry, dusty air damages the lining of the nose and throat, letting bacteria that "
        "many people carry harmlessly reach the bloodstream. Season and geography decide "
        "the risk together, which is why the engine gates this one on both.",
        "Learn the danger signs: stiff neck, high fever, and light hurting the eyes.",
    ),
    lesson(
        HealthCondition.MENINGITIS,
        ADULT_VOICE,
        "Dust, dryness and the danger signs",
        "The Harmattan dries and damages the lining of the nose and throat, which lets "
        "bacteria many people carry without harm reach the bloodstream. Cases appear one "
        "to four weeks after the dust rises. Meningitis moves quickly once it starts, so "
        "recognising it early matters more than anything else.",
        "Go to a clinic the same day for stiff neck, high fever, or eyes hurting in light.",
    ),
    lesson(
        HealthCondition.MENINGITIS,
        ELDER_VOICE,
        "When the Harmattan is heavy",
        "Dry dusty air makes it easier for this illness to take hold. It becomes serious "
        "quickly, so it must not be watched at home.",
        "Cover your nose in dust. Go to the clinic the same day for a stiff neck or strong fever.",
    ),
    # Diarrhoeal disease
    lesson(
        HealthCondition.DIARRHOEAL_DISEASE,
        CHILD_VOICE,
        "Small bodies lose water fast",
        "When a small child has watery stools, water leaves their body much faster than "
        "it leaves yours. That is what makes them weak. A special drink of salt and sugar "
        "in clean water puts it back.",
        "Tell an adult straight away if a younger child has watery stools.",
    ),
    lesson(
        HealthCondition.DIARRHOEAL_DISEASE,
        TEEN_VOICE,
        "The cheapest medicine there is",
        "Oral rehydration salts cost very little and have saved more children's lives than "
        "almost any other treatment. They do not stop the illness; they replace what the "
        "body is losing, which is the part that kills.",
        "Check that your household has rehydration salts, and learn how to mix them.",
    ),
    lesson(
        HealthCondition.DIARRHOEAL_DISEASE,
        ADULT_VOICE,
        "Rain, water and under-fives",
        "Rainfall carries waste into water sources, and diarrhoeal illness follows within "
        "three to fourteen days. Children under five are affected worst because they "
        "dehydrate fastest. Treating the water prevents it; rehydration salts prevent the "
        "deaths when it happens anyway.",
        "Treat drinking water, and keep rehydration salts within reach.",
    ),
    lesson(
        HealthCondition.DIARRHOEAL_DISEASE,
        ELDER_VOICE,
        "Keep rehydration salts at home",
        "Illness that causes watery stools is more likely this week. It takes fluid from "
        "the body quickly, most dangerously in small children.",
        "Keep rehydration salts at home, and give them at the first watery stool.",
    ),
    # Schistosomiasis and dengue: after malaria, the two the engine raises most often in
    # the wet season, so leaving them to the fallback would send most readers a placeholder.
    lesson(
        HealthCondition.SCHISTOSOMIASIS,
        CHILD_VOICE,
        "The snail in the still water",
        "Bilharzia does not come from the water itself. It comes from tiny worms that grow "
        "inside snails living in slow, still water, then swim out and go through your skin. "
        "You feel nothing when it happens.",
        "Do not swim or wade in still ponds or slow streams.",
    ),
    lesson(
        HealthCondition.SCHISTOSOMIASIS,
        TEEN_VOICE,
        "Why bilharzia takes months to show",
        "The parasite enters through unbroken skin in still fresh water, then matures inside "
        "the body for weeks before any sign appears. That long gap is why people connect "
        "the illness to nothing in particular, and why a warning at the time of exposure "
        "matters more than one at the time of symptoms.",
        "Fetch water from a pump or tap rather than a pond, and keep others out of still water.",
    ),
    lesson(
        HealthCondition.SCHISTOSOMIASIS,
        ADULT_VOICE,
        "Standing water that people wade in",
        "Sustained rain expands the slow water where the host snails live. The parasite "
        "passes through skin during ordinary contact, washing, fishing or fetching, and "
        "cases appear four to twelve weeks later. Children in the water daily carry the "
        "heaviest burden.",
        "Keep children out of still water, and use a pump or tap where there is one.",
    ),
    lesson(
        HealthCondition.SCHISTOSOMIASIS,
        ELDER_VOICE,
        "Keep the children out of the pond",
        "Rain has spread the still water where this illness begins. It passes through the "
        "skin of anyone standing in it, and it shows itself only months later.",
        "Keep children from swimming or fishing in still water this season.",
    ),
    lesson(
        HealthCondition.DENGUE,
        CHILD_VOICE,
        "The mosquito that bites in daylight",
        "Not all mosquitoes wait for night. This one bites in the morning and late "
        "afternoon, and it breeds in clean water, in tyres, tins and flower pots close to "
        "the house rather than out in the bush.",
        "Empty and turn over anything near your home holding water.",
    ),
    lesson(
        HealthCondition.DENGUE,
        TEEN_VOICE,
        "Why a net is not enough for dengue",
        "The dengue mosquito bites during the day, so a net at night protects far less than "
        "it does against malaria. It also breeds in clean stored water beside houses, which "
        "means the breeding site is usually inside the compound, not away from it.",
        "Cover stored water and clear containers around your compound.",
    ),
    lesson(
        HealthCondition.DENGUE,
        ADULT_VOICE,
        "A daytime biter breeding in your compound",
        "Dengue is carried by a mosquito that bites in daylight and breeds in clean water "
        "close to homes, so nets and bush clearance help less than they do for malaria. "
        "Cases follow two to six weeks after the rain that filled those containers.",
        "Cover stored water, and empty tyres, tins and pots around the house.",
    ),
    lesson(
        HealthCondition.DENGUE,
        ELDER_VOICE,
        "Cover the water near the house",
        "This fever comes from a mosquito that bites in the daytime and breeds in clean "
        "water kept near homes.",
        "Keep stored water covered, and empty tins and pots around the house.",
    ),
    # Respiratory and heat illness
    lesson(
        HealthCondition.RESPIRATORY_HEAT_ILLNESS,
        CHILD_VOICE,
        "Air you can see",
        "When the air is full of dust or smoke, you are breathing in tiny pieces of it. "
        "They make your chest tight and your throat sore, and they are worst for anyone "
        "who already finds breathing hard.",
        "Play indoors when the air outside looks thick, and never near burning rubbish.",
    ),
    lesson(
        HealthCondition.RESPIRATORY_HEAT_ILLNESS,
        TEEN_VOICE,
        "What burning waste does to a street",
        "Burning rubbish releases particles small enough to travel deep into the lungs. "
        "One fire affects everybody downwind of it, especially people with asthma and "
        "small children, and it lingers long after the flames are out.",
        "Do not burn waste, and tell your household why the smoke matters.",
    ),
    lesson(
        HealthCondition.RESPIRATORY_HEAT_ILLNESS,
        ADULT_VOICE,
        "Heat and bad air arrive together",
        "Extreme heat and heavy dust or smoke both strain the heart and lungs, and they "
        "tend to arrive on the same days. Effects show within one to three days. Older "
        "adults, young children and anyone with asthma or heart disease feel it first.",
        "Stay indoors at midday, drink water often, and keep inhalers close.",
    ),
    lesson(
        HealthCondition.RESPIRATORY_HEAT_ILLNESS,
        ELDER_VOICE,
        "Rest indoors in the worst hours",
        "The air is heavy and the heat is high. Both make the heart and lungs work harder, "
        "and both are felt most by older people.",
        "Rest indoors between midday and three, and drink water even when not thirsty.",
    ),
)

LESSONS_BY_KEY: dict[tuple[HealthCondition, GuardianTier], Lesson] = {
    (entry.condition, entry.tier): entry for entry in LESSONS
}

TIER_FALLBACK_TITLES: dict[GuardianTier, str] = {
    CHILD_VOICE: "What is happening outside",
    TEEN_VOICE: "The signal behind the warning",
    ADULT_VOICE: "What today's weather means",
    ELDER_VOICE: "What to do this week",
}


def fallback(condition: HealthCondition, tier: GuardianTier, action: str) -> Lesson:
    """A written lesson exists for every Tier 1 condition at every age.

    Beyond those, rather than show a nine-year-old an adult's paragraph, we say plainly
    that the detail is not written yet and give the action, which is the part that
    protects somebody today.
    """
    readable = condition.value.replace("_", " ")
    return lesson(
        condition,
        tier,
        TIER_FALLBACK_TITLES[tier],
        f"The engine has raised {readable} in your district from this week's weather. "
        "A full lesson for your age is still being written, so here is the part that "
        "matters most today.",
        action,
    )


def lesson_for(condition: HealthCondition, tier: GuardianTier, fallback_action: str) -> Lesson:
    found = LESSONS_BY_KEY.get((condition, tier))
    return found if found is not None else fallback(condition, tier, fallback_action)
