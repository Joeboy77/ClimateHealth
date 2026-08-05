from datetime import date

from climahealth.domain.models import HealthCondition
from climahealth.services.citizens import GuardianTier
from climahealth.services.gamification_service import (
    Guardian,
    GuardianLevel,
    Mission,
    QuizQuestion,
)

GUARDIAN_LADDER: tuple[GuardianLevel, ...] = (
    GuardianLevel(name="Watcher", minimum_points=0, unlocks="The daily hazard quiz"),
    GuardianLevel(name="Reporter", minimum_points=100, unlocks="Reporting hazards with photos"),
    GuardianLevel(name="Defender", minimum_points=300, unlocks="The community mission board"),
    GuardianLevel(
        name="Guardian", minimum_points=700, unlocks="Contributing to your district shield"
    ),
    GuardianLevel(name="Champion", minimum_points=1500, unlocks="The regional leaderboard"),
)

SEEDED_MISSIONS: tuple[Mission, ...] = (
    Mission(
        mission_id="clear-standing-water",
        description="Clear standing water around your home",
        points=30,
    ),
    Mission(
        mission_id="hang-treated-net",
        description="Hang and check a treated mosquito net",
        points=25,
    ),
    Mission(
        mission_id="treat-drinking-water",
        description="Boil or treat your household drinking water",
        points=20,
    ),
    Mission(
        mission_id="share-forecast",
        description="Share today's forecast with three neighbours",
        points=15,
    ),
    Mission(
        mission_id="report-a-hazard",
        description="Submit a hazard report from your community",
        points=40,
    ),
)

SEEDED_GUARDIANS: tuple[Guardian, ...] = (
    Guardian(
        user_id="user-madina",
        display_name="Madina District Health Officer",
        district_id="madina",
        points=340,
        completed_mission_ids=("clear-standing-water", "share-forecast"),
    ),
    Guardian(
        user_id="user-national",
        display_name="National Surveillance Officer",
        district_id="madina",
        points=820,
        completed_mission_ids=("hang-treated-net",),
    ),
    Guardian(
        user_id="citizen-0417",
        display_name="Ama",
        district_id="madina",
        points=145,
        completed_mission_ids=("report-a-hazard",),
    ),
    Guardian(
        user_id="citizen-1120",
        display_name="Fuseina",
        district_id="wa",
        points=60,
        completed_mission_ids=(),
    ),
)

OUTBREAKS_AVERTED: dict[str, int] = {"madina": 3, "wa": 2, "tamale": 1}

QUIZ_BANK: tuple[QuizQuestion, ...] = (
    QuizQuestion(
        question_id="malaria-1",
        condition=HealthCondition.MALARIA,
        prompt="After heavy rain, what is the single best thing to do around your home?",
        options=(
            "Empty containers holding standing water",
            "Close all the windows during the day",
            "Boil drinking water for longer",
            "Wear a face covering outdoors",
        ),
        correct_option_index=0,
        explanation=(
            "Mosquitoes breed in standing water. Emptying containers after rain removes "
            "the breeding sites before the mosquitoes emerge."
        ),
    ),
    QuizQuestion(
        question_id="malaria-2",
        condition=HealthCondition.MALARIA,
        prompt="How long after heavy rain do malaria cases usually start to rise?",
        options=("Within two days", "About three to eight weeks", "Six months", "The same night"),
        correct_option_index=1,
        explanation=(
            "Mosquitoes need time to breed and the parasite needs time to develop, so cases "
            "typically rise three to eight weeks after the rain."
        ),
    ),
    QuizQuestion(
        question_id="cholera-1",
        condition=HealthCondition.CHOLERA,
        prompt="Flooding has contaminated the area. What should you do with drinking water?",
        options=(
            "Let it settle and drink the clear part",
            "Boil or treat it before drinking",
            "Add sugar and salt to it",
            "Store it in the sun for a day",
        ),
        correct_option_index=1,
        explanation=(
            "Cholera spreads through contaminated water. Boiling or treating water kills "
            "the bacteria; letting it settle does not."
        ),
    ),
    QuizQuestion(
        question_id="meningitis-1",
        condition=HealthCondition.MENINGITIS,
        prompt="During harmattan, which symptom combination needs a clinic urgently?",
        options=(
            "Fever with a stiff neck",
            "Sneezing and a runny nose",
            "Dry skin and thirst",
            "Tiredness after work",
        ),
        correct_option_index=0,
        explanation=(
            "Fever with a stiff neck is a warning sign of meningitis. Treatment is most "
            "effective when it starts early, so go to a clinic straight away."
        ),
    ),
    QuizQuestion(
        question_id="meningitis-2",
        condition=HealthCondition.MENINGITIS,
        prompt="Why does meningitis risk rise during the dry, dusty season?",
        options=(
            "Dust and dry air damage the lining of the nose and throat",
            "Mosquitoes carry the infection",
            "Food spoils faster in the heat",
            "Water sources dry up",
        ),
        correct_option_index=0,
        explanation=(
            "Dry, dusty air damages the mucous barrier in the nose and throat that normally "
            "blocks the bacteria from entering the body."
        ),
    ),
    QuizQuestion(
        question_id="diarrhoeal-1",
        condition=HealthCondition.DIARRHOEAL_DISEASE,
        prompt="A child has diarrhoea. What should be given first?",
        options=(
            "Oral rehydration salts",
            "Nothing until the diarrhoea stops",
            "Only solid food",
            "A cold bath",
        ),
        correct_option_index=0,
        explanation=(
            "Dehydration is what makes diarrhoea dangerous for children. Oral rehydration "
            "salts replace the lost fluid and salts, and should start early."
        ),
    ),
    QuizQuestion(
        question_id="respiratory-1",
        condition=HealthCondition.RESPIRATORY_HEAT_ILLNESS,
        prompt="On a very hot, dusty day, what protects you best?",
        options=(
            "Stay out of the midday sun, drink water often, and cover your nose",
            "Exercise outdoors to build tolerance",
            "Drink only when you feel thirsty",
            "Keep all windows shut all day",
        ),
        correct_option_index=0,
        explanation=(
            "Heat illness builds up before you feel it. Avoiding midday sun, drinking water "
            "regularly, and covering your nose against dust all reduce the strain."
        ),
    ),
)


class InMemoryGuardianStore:
    def __init__(
        self,
        guardians: tuple[Guardian, ...] = SEEDED_GUARDIANS,
        missions: tuple[Mission, ...] = SEEDED_MISSIONS,
        ladder: tuple[GuardianLevel, ...] = GUARDIAN_LADDER,
        averted: dict[str, int] | None = None,
    ) -> None:
        self._guardians = {guardian.user_id: guardian for guardian in guardians}
        self._missions = {mission.mission_id: mission for mission in missions}
        self._ladder = ladder
        self._averted = dict(averted if averted is not None else OUTBREAKS_AVERTED)

    def enrol(self, user_id: str, display_name: str, district_id: str) -> Guardian:
        """Joining Dawuro is becoming a Guardian: there is no second sign-up.

        Proposal section 11: everyone who joins becomes a Climate Guardian of their
        district. Without this, a newly registered citizen has nowhere for points to go
        and the first quiz answer fails.
        """
        existing = self._guardians.get(user_id)
        if existing is not None:
            return existing
        guardian = Guardian(
            user_id=user_id,
            display_name=display_name,
            district_id=district_id,
            points=0,
        )
        self._guardians[user_id] = guardian
        return guardian

    def find(self, user_id: str) -> Guardian | None:
        return self._guardians.get(user_id)

    def for_district(self, district_id: str) -> tuple[Guardian, ...]:
        return tuple(
            guardian for guardian in self._guardians.values() if guardian.district_id == district_id
        )

    def ladder(self) -> tuple[GuardianLevel, ...]:
        return self._ladder

    def find_mission(self, mission_id: str) -> Mission | None:
        return self._missions.get(mission_id)

    def record_mission(self, user_id: str, mission: Mission) -> Guardian:
        guardian = self._guardians[user_id]
        updated = guardian.model_copy(
            update={
                "points": guardian.points + mission.points,
                "completed_mission_ids": (
                    *guardian.completed_mission_ids,
                    mission.mission_id,
                ),
            }
        )
        self._guardians[user_id] = updated
        return updated

    def record_quiz_answer(self, user_id: str, question_id: str, points: int) -> Guardian:
        guardian = self._guardians[user_id]
        answered = guardian.answered_question_ids
        updated = guardian.model_copy(
            update={
                "points": guardian.points + points,
                "answered_question_ids": (
                    answered if question_id in answered else (*answered, question_id)
                ),
            }
        )
        self._guardians[user_id] = updated
        return updated

    def outbreaks_averted(self, district_id: str) -> int:
        return self._averted.get(district_id, 0)


class InMemoryQuizRepository:
    def __init__(self, questions: tuple[QuizQuestion, ...] | None = None) -> None:
        questions = questions if questions is not None else QUIZ_BANK
        self._questions = questions
        self._by_id = {question.question_id: question for question in questions}

    def question_for(
        self,
        condition: HealthCondition,
        day: date,
        tier: GuardianTier | None = None,
    ) -> QuizQuestion:
        """The right condition first, then the right age, then anything.

        A question written for this tier always beats an untiered one, so a nine-year-old
        is never asked an adult's wording just because it came first in the bank.
        """
        matching = [question for question in self._questions if question.condition is condition]
        if not matching:
            matching = list(self._questions)

        for_tier = [question for question in matching if question.tier is tier]
        untiered = [question for question in matching if question.tier is None]
        candidates = for_tier or untiered or matching
        return candidates[day.toordinal() % len(candidates)]

    def find(self, question_id: str) -> QuizQuestion | None:
        return self._by_id.get(question_id)


# Written for the youngest and oldest readers, who are least served by the wording that
# suits an adult. Where no tiered question exists the untiered bank still answers.
TIERED_QUIZ_BANK: tuple[QuizQuestion, ...] = (
    QuizQuestion(
        question_id="malaria-child-1",
        condition=HealthCondition.MALARIA,
        tier=GuardianTier.ANANSI,
        prompt="Where do mosquitoes lay their eggs?",
        options=(
            "In water that is not moving",
            "In dry sand",
            "On the roof",
            "In the fire",
        ),
        correct_option_index=0,
        explanation=(
            "Mosquitoes need still water for their eggs. Pour out any water sitting in "
            "buckets or tins and the eggs go with it."
        ),
    ),
    QuizQuestion(
        question_id="malaria-elder-1",
        condition=HealthCondition.MALARIA,
        tier=GuardianTier.VOICE_FIRST,
        prompt="What protects you best while you sleep?",
        options=(
            "A treated mosquito net",
            "Keeping a light on",
            "Closing the windows only",
            "Sleeping later",
        ),
        correct_option_index=0,
        explanation=(
            "A treated net is the strongest protection at night, when these mosquitoes bite most."
        ),
    ),
    QuizQuestion(
        question_id="cholera-child-1",
        condition=HealthCondition.CHOLERA,
        tier=GuardianTier.ANANSI,
        prompt="Water that makes you sick always looks dirty. True or false?",
        options=(
            "False, it can look clean",
            "True, it is always brown",
            "Only at night",
            "Only in the rain",
        ),
        correct_option_index=0,
        explanation=(
            "You cannot see, smell or taste what makes water unsafe. Boiling it is what "
            "makes it safe."
        ),
    ),
    QuizQuestion(
        question_id="cholera-elder-1",
        condition=HealthCondition.CHOLERA,
        tier=GuardianTier.VOICE_FIRST,
        prompt="Someone has watery stools. What should be given first?",
        options=(
            "Rehydration salts in clean water",
            "Only food",
            "Nothing until tomorrow",
            "Strong tea",
        ),
        correct_option_index=0,
        explanation=(
            "Rehydration salts replace what the body is losing. Give them at once and go "
            "to the clinic the same day."
        ),
    ),
    QuizQuestion(
        question_id="meningitis-child-1",
        condition=HealthCondition.MENINGITIS,
        tier=GuardianTier.ANANSI,
        prompt="When the dusty wind blows, what helps keep you safe?",
        options=(
            "Covering your nose with a cloth",
            "Running faster",
            "Drinking cold water",
            "Standing in the wind",
        ),
        correct_option_index=0,
        explanation=(
            "Dust dries the inside of your nose, which lets germs in. Covering your nose "
            "keeps the dust out."
        ),
    ),
    QuizQuestion(
        question_id="meningitis-elder-1",
        condition=HealthCondition.MENINGITIS,
        tier=GuardianTier.VOICE_FIRST,
        prompt="Which sign means going to the clinic today, not tomorrow?",
        options=(
            "A stiff neck with fever",
            "A small cough",
            "Feeling tired",
            "A dry mouth",
        ),
        correct_option_index=0,
        explanation=(
            "A stiff neck with fever can mean meningitis, which moves very quickly. It "
            "must be seen the same day."
        ),
    ),
)

EXTENDED_QUIZ_BANK: tuple[QuizQuestion, ...] = (
    QuizQuestion(
        question_id="dengue-1",
        condition=HealthCondition.DENGUE,
        prompt="Dengue mosquitoes differ from malaria mosquitoes in one important way. Which?",
        options=(
            "They bite during the day, not at night",
            "They only live in rivers",
            "They cannot fly indoors",
            "They only bite adults",
        ),
        correct_option_index=0,
        explanation=(
            "Aedes mosquitoes bite in daylight, so a bed net alone will not protect you. "
            "Repellent during the day and emptying water containers both matter."
        ),
    ),
    QuizQuestion(
        question_id="typhoid_fever-1",
        condition=HealthCondition.TYPHOID_FEVER,
        prompt="After flooding, what is the safest source of drinking water?",
        options=(
            "Water you have boiled or treated",
            "Rain collected off any roof",
            "The clearest-looking stream",
            "Well water without treatment",
        ),
        correct_option_index=0,
        explanation=(
            "Typhoid spreads through water contaminated with sewage. Clear water can still "
            "carry it, so boiling or treating is what makes it safe."
        ),
    ),
    QuizQuestion(
        question_id="schistosomiasis-1",
        condition=HealthCondition.SCHISTOSOMIASIS,
        prompt="How do people catch bilharzia?",
        options=(
            "Skin contact with slow-moving fresh water",
            "Breathing dusty air",
            "Mosquito bites",
            "Eating undercooked meat",
        ),
        correct_option_index=0,
        explanation=(
            "The parasite leaves freshwater snails and enters through the skin, so wading, "
            "swimming or washing in still water is the risk."
        ),
    ),
    QuizQuestion(
        question_id="lassa_fever-1",
        condition=HealthCondition.LASSA_FEVER,
        prompt="How does Lassa fever usually reach a household?",
        options=(
            "Food or surfaces contaminated by rats",
            "Mosquito bites at night",
            "Drinking rain water",
            "Dust blown from the north",
        ),
        correct_option_index=0,
        explanation=(
            "Lassa spreads from multimammate rats through their urine and droppings. "
            "Sealed food storage and blocking rat entry are the main defences."
        ),
    ),
    QuizQuestion(
        question_id="yellow_fever-1",
        condition=HealthCondition.YELLOW_FEVER,
        prompt="What is the strongest protection against yellow fever?",
        options=(
            "Vaccination",
            "Boiling water",
            "Wearing a face covering",
            "Taking antimalarials",
        ),
        correct_option_index=0,
        explanation=(
            "A single yellow fever vaccination gives long-lasting protection. Clearing "
            "standing water reduces the mosquitoes that carry it."
        ),
    ),
    QuizQuestion(
        question_id="leptospirosis-1",
        condition=HealthCondition.LEPTOSPIROSIS,
        prompt="Why is wading through flood water with an open cut risky?",
        options=(
            "Bacteria in animal urine can enter through broken skin",
            "The water is too cold",
            "Mosquitoes breed in it",
            "It causes dehydration",
        ),
        correct_option_index=0,
        explanation=(
            "Leptospira bacteria spread in water contaminated by rodent urine and enter "
            "through cuts or the eyes and mouth. Cover wounds before wading."
        ),
    ),
    QuizQuestion(
        question_id="trachoma-1",
        condition=HealthCondition.TRACHOMA,
        prompt="What simple habit most reduces trachoma in children?",
        options=(
            "Washing their faces every day",
            "Wearing sunglasses",
            "Drinking more water",
            "Sleeping under a net",
        ),
        correct_option_index=0,
        explanation=(
            "Trachoma spreads through discharge from infected eyes, carried by hands and "
            "flies. Daily face washing and latrine use break that chain."
        ),
    ),
    QuizQuestion(
        question_id="heat_stroke-1",
        condition=HealthCondition.HEAT_STROKE,
        prompt="Someone working outdoors stops sweating and becomes confused. What is happening?",
        options=(
            "Heat stroke — cool them and get help immediately",
            "They are simply tired",
            "They need more salt only",
            "They have malaria",
        ),
        correct_option_index=0,
        explanation=(
            "Stopping sweating and confusion are signs the body can no longer cool itself. "
            "Move to shade, cool with water, and seek help urgently."
        ),
    ),
)

QUIZ_BANK = (*QUIZ_BANK, *EXTENDED_QUIZ_BANK, *TIERED_QUIZ_BANK)


AIR_QUALITY_QUIZ: tuple[QuizQuestion, ...] = (
    QuizQuestion(
        question_id="air_pollution_cardiorespiratory-1",
        condition=HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY,
        prompt="On a day when the air is thick with dust and smoke, who is most at risk?",
        options=(
            "Children, older adults and people with heart or lung conditions",
            "Only people who work outdoors",
            "Only people who smoke",
            "Nobody, dust is harmless",
        ),
        correct_option_index=0,
        explanation=(
            "Fine particles reach deep into the lungs and the bloodstream. Children, "
            "older adults and anyone with heart or lung disease feel it first and worst."
        ),
    ),
)

QUIZ_BANK = (*QUIZ_BANK, *AIR_QUALITY_QUIZ)
