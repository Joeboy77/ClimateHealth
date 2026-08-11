from datetime import date

from climahealth.domain.models import HealthCondition
from climahealth.services.citizens import GuardianTier
from climahealth.services.gamification_service import (
    Guardian,
    GuardianLevel,
    Mission,
    QuizQuestion,
)
from climahealth.services.quiz_session import Streak

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

    def record_session(
        self, user_id: str, question_ids: tuple[str, ...], points: int, streak: Streak
    ) -> Guardian:
        guardian = self._guardians[user_id]
        updated = guardian.model_copy(
            update={
                "points": guardian.points + points,
                "answered_question_ids": tuple({*guardian.answered_question_ids, *question_ids}),
                "streak": streak,
            }
        )
        self._guardians[user_id] = updated
        return updated

    def spend_points(self, user_id: str, points: int) -> Guardian:
        guardian = self._guardians[user_id]
        updated = guardian.model_copy(update={"points": max(guardian.points - points, 0)})
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

    def session_for(
        self,
        condition: HealthCondition,
        day: date,
        tier: GuardianTier | None,
        length: int,
    ) -> tuple[QuizQuestion, ...]:
        """A run of distinct questions about today's hazard, pitched at the reader.

        Rotated by the date so the same person does not meet the same run tomorrow, and
        topped up from the wider bank when one condition has too few written for a tier.
        """
        matching = [q for q in self._questions if q.condition is condition]
        for_tier = [q for q in matching if q.tier is tier]
        untiered = [q for q in matching if q.tier is None]
        pool = [*for_tier, *untiered] or matching or list(self._questions)

        if len(pool) < length:
            extra = [q for q in self._questions if q not in pool and q.tier in (tier, None)]
            pool = [*pool, *extra]

        offset = day.toordinal() % max(len(pool), 1)
        rotated = pool[offset:] + pool[:offset]
        return tuple(rotated[:length])

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


# A session asks three to five questions, so the bank has to carry that every day without
# repeating. These are written per condition and, where the wording would otherwise be
# wrong for the reader, per tier.
SESSION_QUIZ_BANK: tuple[QuizQuestion, ...] = (
    QuizQuestion(
        question_id="malaria-5",
        condition=HealthCondition.MALARIA,
        prompt="Which container is most likely to breed mosquitoes?",
        options=(
            "An open bucket of rainwater",
            "A sealed water tank",
            "A running gutter",
            "A dry basin",
        ),
        correct_option_index=0,
        explanation=(
            "Mosquitoes need water that is still and open. Sealed or moving water does not breed "
            "them."
        ),
    ),
    QuizQuestion(
        question_id="malaria-3",
        condition=HealthCondition.MALARIA,
        prompt="When do malaria mosquitoes bite most?",
        options=("At night", "At midday", "Only in the rain", "Only indoors"),
        correct_option_index=0,
        explanation=(
            "They bite mostly at night, which is why a treated net over the bed matters so much."
        ),
    ),
    QuizQuestion(
        question_id="malaria-4",
        condition=HealthCondition.MALARIA,
        prompt="Who is at greatest risk from malaria?",
        options=(
            "Children under five and pregnant women",
            "Only older men",
            "Only visitors",
            "Everyone equally",
        ),
        correct_option_index=0,
        explanation=(
            "Children under five and pregnant women carry the heaviest burden and should be "
            "protected first."
        ),
    ),
    QuizQuestion(
        question_id="cholera-2",
        condition=HealthCondition.CHOLERA,
        prompt="How quickly can cholera make someone dangerously ill?",
        options=("Within a day", "After a month", "Only after a year", "It never does"),
        correct_option_index=0,
        explanation=(
            "Cholera dehydrates fast, sometimes within hours. That speed is what makes it "
            "dangerous."
        ),
    ),
    QuizQuestion(
        question_id="cholera-3",
        condition=HealthCondition.CHOLERA,
        prompt="What makes flood water dangerous to drink?",
        options=(
            "It mixes with waste from drains",
            "It is too cold",
            "It has too much salt",
            "It is always safe once boiled for a second",
        ),
        correct_option_index=0,
        explanation=(
            "Flooding carries waste into wells and standpipes. Boiling properly is what makes it "
            "safe."
        ),
    ),
    QuizQuestion(
        question_id="meningitis-5",
        condition=HealthCondition.MENINGITIS,
        prompt="Why does the Harmattan raise meningitis risk?",
        options=(
            "Dry dusty air damages the nose and throat",
            "It brings more mosquitoes",
            "It makes water unsafe",
            "It has no effect",
        ),
        correct_option_index=0,
        explanation=(
            "Dry air damages the lining of the nose and throat, letting bacteria reach the "
            "bloodstream."
        ),
    ),
    QuizQuestion(
        question_id="meningitis-3",
        condition=HealthCondition.MENINGITIS,
        prompt="How soon should a stiff neck with fever be seen?",
        options=("The same day", "Within a month", "Only if it lasts a week", "It clears itself"),
        correct_option_index=0,
        explanation=(
            "Meningitis moves very quickly. A stiff neck with fever is a same-day clinic visit."
        ),
    ),
    QuizQuestion(
        question_id="diarrhoeal-2",
        condition=HealthCondition.DIARRHOEAL_DISEASE,
        prompt="What should be given first for watery stools in a child?",
        options=(
            "Oral rehydration salts",
            "Only solid food",
            "Nothing until morning",
            "Sugary soft drinks",
        ),
        correct_option_index=0,
        explanation=(
            "Rehydration salts replace what the body is losing. That loss is what kills, not the "
            "germ alone."
        ),
    ),
    QuizQuestion(
        question_id="diarrhoeal-3",
        condition=HealthCondition.DIARRHOEAL_DISEASE,
        prompt="Who is most at risk when diarrhoeal illness rises?",
        options=("Children under five", "Teenagers", "Adult men", "Nobody in particular"),
        correct_option_index=0,
        explanation="Small children dehydrate fastest, which is why they are affected worst.",
    ),
    QuizQuestion(
        question_id="schistosomiasis-2",
        condition=HealthCondition.SCHISTOSOMIASIS,
        prompt="How does bilharzia enter the body?",
        options=(
            "Through skin in still fresh water",
            "By breathing dust",
            "From mosquito bites",
            "Only from food",
        ),
        correct_option_index=0,
        explanation=(
            "The parasite passes through unbroken skin during contact with slow or still fresh "
            "water."
        ),
    ),
    QuizQuestion(
        question_id="schistosomiasis-3",
        condition=HealthCondition.SCHISTOSOMIASIS,
        prompt="Why is bilharzia often missed?",
        options=(
            "Signs appear weeks or months later",
            "It causes no illness",
            "It only affects adults",
            "It clears in a day",
        ),
        correct_option_index=0,
        explanation=(
            "The long gap between exposure and symptoms is why people rarely connect the two."
        ),
    ),
    QuizQuestion(
        question_id="dengue-2",
        condition=HealthCondition.DENGUE,
        prompt="When does the dengue mosquito bite?",
        options=("In daylight", "Only at midnight", "Only in harmattan", "It does not bite"),
        correct_option_index=0,
        explanation=(
            "It bites during the day, so a net at night protects far less than it does against "
            "malaria."
        ),
    ),
    QuizQuestion(
        question_id="heat-2",
        condition=HealthCondition.HEAT_STROKE,
        prompt="What is the best protection during extreme heat?",
        options=(
            "Rest in shade and drink water often",
            "Work faster to finish early",
            "Drink only when thirsty",
            "Wear heavy clothing",
        ),
        correct_option_index=0,
        explanation=(
            "Rest in the hottest hours and drink before you feel thirsty. Thirst arrives late."
        ),
    ),
    QuizQuestion(
        question_id="airpollution-2",
        condition=HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY,
        prompt="Who feels bad air first?",
        options=(
            "People with asthma, young children and older adults",
            "Only farmers",
            "Only people outdoors at night",
            "Nobody notices",
        ),
        correct_option_index=0,
        explanation="Small particles reach deep into the lungs and affect those groups soonest.",
    ),
    QuizQuestion(
        question_id="malaria-child-2",
        condition=HealthCondition.MALARIA,
        tier=GuardianTier.ANANSI,
        prompt="What should you do with a bucket of old rain water?",
        options=("Pour it away", "Leave it for later", "Add more water", "Cover the yard"),
        correct_option_index=0,
        explanation="Pouring it away takes the mosquito eggs with it.",
    ),
    QuizQuestion(
        question_id="malaria-elder-2",
        condition=HealthCondition.MALARIA,
        tier=GuardianTier.VOICE_FIRST,
        prompt="Who in the house should sleep under a net first?",
        options=(
            "Small children and pregnant women",
            "Only visitors",
            "Only the eldest",
            "Nobody needs one",
        ),
        correct_option_index=0,
        explanation="They carry the greatest risk from malaria and should be covered first.",
    ),
    QuizQuestion(
        question_id="cholera-child-2",
        condition=HealthCondition.CHOLERA,
        tier=GuardianTier.ANANSI,
        prompt="When should you wash your hands with soap?",
        options=("Before eating", "Only on Sunday", "Only after playing", "Never"),
        correct_option_index=0,
        explanation=(
            "Washing with soap before eating stops germs going from your hands into your food."
        ),
    ),
    QuizQuestion(
        question_id="schisto-child-1",
        condition=HealthCondition.SCHISTOSOMIASIS,
        tier=GuardianTier.ANANSI,
        prompt="Is it safe to swim in a still pond?",
        options=(
            "No, tiny worms can get in through your skin",
            "Yes, always",
            "Only at night",
            "Only if it is deep",
        ),
        correct_option_index=0,
        explanation=(
            "Still ponds can hold the snails that carry bilharzia. The worms go through your skin."
        ),
    ),
    QuizQuestion(
        question_id="schisto-elder-1",
        condition=HealthCondition.SCHISTOSOMIASIS,
        tier=GuardianTier.VOICE_FIRST,
        prompt="What is the safest place to fetch water this season?",
        options=("A pump or tap", "A slow stream", "A still pond", "A flooded field"),
        correct_option_index=0,
        explanation="A pump or tap avoids the still water where this illness begins.",
    ),
)


# Every condition the engine can raise now carries enough questions for a run of five
# without borrowing from an unrelated hazard.
DEPTH_QUIZ_BANK: tuple[QuizQuestion, ...] = (
    QuizQuestion(
        question_id="dengue-3",
        condition=HealthCondition.DENGUE,
        prompt="Where does the dengue mosquito usually breed?",
        options=(
            "In clean water stored near houses",
            "In deep rivers",
            "In salty water",
            "In dry soil",
        ),
        correct_option_index=0,
        explanation=(
            "It breeds in clean stored water close to homes, which is why the breeding site is "
            "usually inside the compound."
        ),
    ),
    QuizQuestion(
        question_id="dengue-4",
        condition=HealthCondition.DENGUE,
        prompt="Why does a bed net help less against dengue than malaria?",
        options=(
            "The mosquito bites during the day",
            "Nets do not work on it",
            "It does not bite people",
            "It only bites animals",
        ),
        correct_option_index=0,
        explanation="Dengue mosquitoes bite in daylight, so a net used at night protects far less.",
    ),
    QuizQuestion(
        question_id="dengue-5",
        condition=HealthCondition.DENGUE,
        prompt="What is the best action around the house?",
        options=(
            "Cover stored water and empty containers",
            "Cut down all trees",
            "Close windows at night only",
            "Nothing works",
        ),
        correct_option_index=0,
        explanation=(
            "Covering stored water and emptying tyres, tins and pots removes the places they breed."
        ),
    ),
    QuizQuestion(
        question_id="dengue-6",
        condition=HealthCondition.DENGUE,
        prompt="Who should be watched most closely for dengue fever?",
        options=(
            "Anyone with high fever and severe body pain",
            "Only newborns",
            "Only farmers",
            "Only travellers",
        ),
        correct_option_index=0,
        explanation="High fever with severe joint and muscle pain needs a clinic, whoever it is.",
    ),
    QuizQuestion(
        question_id="diarrhoeal-4",
        condition=HealthCondition.DIARRHOEAL_DISEASE,
        prompt="How do rehydration salts help?",
        options=(
            "They replace the fluid the body is losing",
            "They kill the germ",
            "They stop hunger",
            "They lower fever only",
        ),
        correct_option_index=0,
        explanation=(
            "They do not cure the illness. They replace what is being lost, and that loss is "
            "what kills."
        ),
    ),
    QuizQuestion(
        question_id="diarrhoeal-5",
        condition=HealthCondition.DIARRHOEAL_DISEASE,
        prompt="How soon after heavy rain can diarrhoeal illness rise?",
        options=(
            "Within three to fourteen days",
            "After a year",
            "Only in the dry season",
            "It never follows rain",
        ),
        correct_option_index=0,
        explanation=(
            "Rain carries waste into water sources, and illness follows within three to "
            "fourteen days."
        ),
    ),
    QuizQuestion(
        question_id="diarrhoeal-6",
        condition=HealthCondition.DIARRHOEAL_DISEASE,
        prompt="What makes drinking water safe at home?",
        options=(
            "Boiling it or treating it properly",
            "Leaving it in the sun for a minute",
            "Adding sugar",
            "Straining it through cloth alone",
        ),
        correct_option_index=0,
        explanation=(
            "Boiling or proper treatment is what makes water safe. Straining removes dirt, not "
            "germs."
        ),
    ),
    QuizQuestion(
        question_id="heat-3",
        condition=HealthCondition.HEAT_STROKE,
        prompt="When should outdoor work be avoided in extreme heat?",
        options=(
            "Between midday and mid afternoon",
            "Early morning",
            "After sunset",
            "It never matters",
        ),
        correct_option_index=0,
        explanation=(
            "The hours around midday carry the most heat stress. Shift heavy work to the cooler "
            "ends of the day."
        ),
    ),
    QuizQuestion(
        question_id="heat-4",
        condition=HealthCondition.HEAT_STROKE,
        prompt="What is a danger sign of heat stroke?",
        options=(
            "Confusion or fainting",
            "A mild thirst",
            "Slight tiredness",
            "Sweating a little",
        ),
        correct_option_index=0,
        explanation="Confusion, fainting or hot dry skin mean heat stroke, which is an emergency.",
    ),
    QuizQuestion(
        question_id="heat-5",
        condition=HealthCondition.HEAT_STROKE,
        prompt="When should you drink water in high heat?",
        options=(
            "Regularly, before you feel thirsty",
            "Only when very thirsty",
            "Only at meals",
            "Only after work",
        ),
        correct_option_index=0,
        explanation="Thirst arrives late. Drinking regularly through the day is what protects you.",
    ),
    QuizQuestion(
        question_id="heat-6",
        condition=HealthCondition.HEAT_STROKE,
        prompt="Who suffers heat illness first?",
        options=(
            "Older adults, small children and outdoor workers",
            "Only teenagers",
            "Only office workers",
            "Everyone equally",
        ),
        correct_option_index=0,
        explanation=(
            "Those groups lose heat least easily or are exposed longest, so they feel it first."
        ),
    ),
    QuizQuestion(
        question_id="airpollution-3",
        condition=HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY,
        prompt="Why is burning household waste harmful?",
        options=(
            "It releases particles that reach deep into the lungs",
            "It uses too much fuel",
            "It is only a smell",
            "It only affects plants",
        ),
        correct_option_index=0,
        explanation=(
            "Burning waste releases fine particles that travel deep into the lungs and affect "
            "everyone downwind."
        ),
    ),
    QuizQuestion(
        question_id="airpollution-4",
        condition=HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY,
        prompt="What helps on a heavy dust or smoke day?",
        options=(
            "Stay indoors and keep windows shut when air is thick",
            "Exercise outside",
            "Burn more waste",
            "Open all doors",
        ),
        correct_option_index=0,
        explanation=(
            "Reducing the air you take in during the worst hours is the practical protection."
        ),
    ),
    QuizQuestion(
        question_id="airpollution-5",
        condition=HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY,
        prompt="Who should keep medicine close when air quality drops?",
        options=(
            "People with asthma or heart disease",
            "Only children",
            "Only the elderly",
            "Nobody",
        ),
        correct_option_index=0,
        explanation=(
            "Bad air strains the lungs and heart first in people who already have trouble with "
            "either."
        ),
    ),
    QuizQuestion(
        question_id="airpollution-6",
        condition=HealthCondition.AIR_POLLUTION_CARDIORESPIRATORY,
        prompt="What is the safest way to deal with household rubbish?",
        options=(
            "Proper collection or disposal, never burning",
            "Burn it at night",
            "Burn it far from the house",
            "Bury it while burning",
        ),
        correct_option_index=0,
        explanation="Burning is what releases the particles. Proper disposal avoids that entirely.",
    ),
    QuizQuestion(
        question_id="respiratory-2",
        condition=HealthCondition.RESPIRATORY_HEAT_ILLNESS,
        prompt="What makes breathing harder during Harmattan?",
        options=(
            "Fine dust in the air",
            "Cold rain",
            "High humidity",
            "Still water",
        ),
        correct_option_index=0,
        explanation="Harmattan carries fine dust that irritates the airway and worsens asthma.",
    ),
    QuizQuestion(
        question_id="respiratory-3",
        condition=HealthCondition.RESPIRATORY_HEAT_ILLNESS,
        prompt="What should someone with asthma do when dust is heavy?",
        options=(
            "Keep an inhaler close and stay indoors",
            "Exercise outdoors",
            "Stop medication",
            "Ignore it",
        ),
        correct_option_index=0,
        explanation=(
            "Dusty days are when an inhaler matters most. Staying indoors reduces exposure."
        ),
    ),
    QuizQuestion(
        question_id="respiratory-4",
        condition=HealthCondition.RESPIRATORY_HEAT_ILLNESS,
        prompt="Which group is most affected by dusty air?",
        options=(
            "Older adults, young children and people with asthma",
            "Only adults",
            "Only men",
            "Nobody in particular",
        ),
        correct_option_index=0,
        explanation="Those groups have the least reserve when the airway is irritated.",
    ),
    QuizQuestion(
        question_id="respiratory-5",
        condition=HealthCondition.RESPIRATORY_HEAT_ILLNESS,
        prompt="Does covering the nose in heavy dust help?",
        options=(
            "Yes, a cloth over the nose reduces what you breathe in",
            "No, it makes it worse",
            "Only at night",
            "Only for children",
        ),
        correct_option_index=0,
        explanation="A cloth over the nose and mouth cuts how much dust reaches the airway.",
    ),
    QuizQuestion(
        question_id="respiratory-6",
        condition=HealthCondition.RESPIRATORY_HEAT_ILLNESS,
        prompt="When is dusty air usually worst in Ghana?",
        options=(
            "In the dry season Harmattan",
            "During heavy rain",
            "At the coast in June",
            "It is the same all year",
        ),
        correct_option_index=0,
        explanation="The Harmattan blows dry dusty air down from the north in the dry season.",
    ),
    QuizQuestion(
        question_id="yellowfever-2",
        condition=HealthCondition.YELLOW_FEVER,
        prompt="What is the strongest protection against yellow fever?",
        options=(
            "Vaccination",
            "Drinking boiled water",
            "Wearing a hat",
            "Avoiding fruit",
        ),
        correct_option_index=0,
        explanation="Yellow fever is vaccine preventable, and one dose gives long protection.",
    ),
    QuizQuestion(
        question_id="yellowfever-3",
        condition=HealthCondition.YELLOW_FEVER,
        prompt="How does yellow fever spread?",
        options=(
            "Through mosquito bites",
            "Through drinking water",
            "Through dust",
            "Through food",
        ),
        correct_option_index=0,
        explanation=(
            "It is spread by mosquitoes, so avoiding bites and clearing breeding sites both help."
        ),
    ),
    QuizQuestion(
        question_id="yellowfever-4",
        condition=HealthCondition.YELLOW_FEVER,
        prompt="Who should check their vaccination status?",
        options=(
            "Anyone who has never been vaccinated",
            "Only children",
            "Only travellers",
            "Only health workers",
        ),
        correct_option_index=0,
        explanation="Anyone unvaccinated is at risk. Vaccination is the single strongest step.",
    ),
    QuizQuestion(
        question_id="yellowfever-5",
        condition=HealthCondition.YELLOW_FEVER,
        prompt="What reduces mosquito numbers around the home?",
        options=(
            "Emptying containers that hold water",
            "Leaving buckets open",
            "Watering the yard daily",
            "Nothing helps",
        ),
        correct_option_index=0,
        explanation="Removing standing water removes the places mosquitoes breed.",
    ),
    QuizQuestion(
        question_id="typhoid-2",
        condition=HealthCondition.TYPHOID_FEVER,
        prompt="How does typhoid usually spread?",
        options=(
            "Through contaminated food or water",
            "Through mosquito bites",
            "Through dust",
            "Through touch alone",
        ),
        correct_option_index=0,
        explanation="Typhoid spreads through food and water contaminated with waste.",
    ),
    QuizQuestion(
        question_id="typhoid-3",
        condition=HealthCondition.TYPHOID_FEVER,
        prompt="What is the most useful daily habit against typhoid?",
        options=(
            "Washing hands with soap before eating",
            "Drinking cold water",
            "Eating quickly",
            "Avoiding vegetables",
        ),
        correct_option_index=0,
        explanation="Handwashing with soap before eating breaks the route the germ takes.",
    ),
    QuizQuestion(
        question_id="typhoid-4",
        condition=HealthCondition.TYPHOID_FEVER,
        prompt="When does typhoid risk rise?",
        options=(
            "After heavy rain contaminates water",
            "Only in the dry season",
            "Only in cities",
            "Only at the coast",
        ),
        correct_option_index=0,
        explanation="Rain carries waste into water sources, which is when typhoid tends to follow.",
    ),
    QuizQuestion(
        question_id="typhoid-5",
        condition=HealthCondition.TYPHOID_FEVER,
        prompt="What should be done for a fever lasting several days?",
        options=(
            "Go to a clinic to be tested",
            "Wait a month",
            "Treat it as malaria without testing",
            "Ignore it",
        ),
        correct_option_index=0,
        explanation=(
            "A fever lasting days needs testing. Guessing between typhoid and malaria wastes time."
        ),
    ),
    QuizQuestion(
        question_id="lepto-2",
        condition=HealthCondition.LEPTOSPIROSIS,
        prompt="How does leptospirosis usually enter the body?",
        options=(
            "Through skin in contact with flood water",
            "By breathing dust",
            "From mosquito bites",
            "From cooked food",
        ),
        correct_option_index=0,
        explanation=(
            "It enters through skin, especially broken skin, in contact with contaminated flood "
            "water."
        ),
    ),
    QuizQuestion(
        question_id="lepto-3",
        condition=HealthCondition.LEPTOSPIROSIS,
        prompt="Who is most exposed?",
        options=(
            "People wading through flood water",
            "Office workers",
            "Children indoors",
            "Drivers",
        ),
        correct_option_index=0,
        explanation=(
            "Anyone wading through flood water, including farmers and refuse workers, is most "
            "exposed."
        ),
    ),
    QuizQuestion(
        question_id="lepto-4",
        condition=HealthCondition.LEPTOSPIROSIS,
        prompt="What should you do if you must walk through flood water?",
        options=(
            "Cover any wound and wash afterwards",
            "Walk barefoot",
            "Stay in it longer",
            "Nothing special",
        ),
        correct_option_index=0,
        explanation="Covering wounds and washing afterwards reduces the chance of it getting in.",
    ),
    QuizQuestion(
        question_id="lepto-5",
        condition=HealthCondition.LEPTOSPIROSIS,
        prompt="What carries the bacteria into flood water?",
        options=(
            "Animal urine, often from rats",
            "Sea salt",
            "Dust",
            "Sunlight",
        ),
        correct_option_index=0,
        explanation="Animal urine, commonly from rats, contaminates the water that floods carry.",
    ),
    QuizQuestion(
        question_id="lassa-2",
        condition=HealthCondition.LASSA_FEVER,
        prompt="How does Lassa fever reach people?",
        options=(
            "Through food or surfaces contaminated by rats",
            "Through mosquito bites",
            "Through rain",
            "Through dust storms",
        ),
        correct_option_index=0,
        explanation="Rats contaminate food and surfaces, which is why storage matters so much.",
    ),
    QuizQuestion(
        question_id="lassa-3",
        condition=HealthCondition.LASSA_FEVER,
        prompt="What is the best protection at home?",
        options=(
            "Store food in covered containers and keep rats out",
            "Leave grain in the open",
            "Feed the rats",
            "Nothing works",
        ),
        correct_option_index=0,
        explanation=(
            "Covered storage and keeping rats out of the house is the practical protection."
        ),
    ),
    QuizQuestion(
        question_id="lassa-4",
        condition=HealthCondition.LASSA_FEVER,
        prompt="When does Lassa risk usually rise?",
        options=(
            "In the dry season when rats move indoors",
            "In heavy rain only",
            "At the coast",
            "It never changes",
        ),
        correct_option_index=0,
        explanation="Long dry spells push rodents towards houses and stored food.",
    ),
    QuizQuestion(
        question_id="lassa-5",
        condition=HealthCondition.LASSA_FEVER,
        prompt="What should be done for fever with bleeding or severe weakness?",
        options=(
            "Go to a clinic immediately",
            "Wait a week",
            "Treat at home",
            "Ignore it",
        ),
        correct_option_index=0,
        explanation="Those signs need urgent medical care and should never be watched at home.",
    ),
    QuizQuestion(
        question_id="trachoma-2",
        condition=HealthCondition.TRACHOMA,
        prompt="What helps prevent trachoma in children?",
        options=(
            "Washing faces daily and keeping flies away",
            "Wearing sunglasses",
            "Drinking more milk",
            "Sleeping longer",
        ),
        correct_option_index=0,
        explanation=(
            "Clean faces and fewer flies break the way the infection passes between children."
        ),
    ),
    QuizQuestion(
        question_id="trachoma-3",
        condition=HealthCondition.TRACHOMA,
        prompt="How does trachoma spread?",
        options=(
            "Through flies and contact with infected eyes",
            "Through mosquito bites",
            "Through water only",
            "Through dust alone",
        ),
        correct_option_index=0,
        explanation=(
            "It passes through flies and direct contact, which is why face washing matters."
        ),
    ),
    QuizQuestion(
        question_id="trachoma-4",
        condition=HealthCondition.TRACHOMA,
        prompt="Who is most affected by trachoma?",
        options=(
            "Young children and the women who care for them",
            "Only men",
            "Only the elderly",
            "Only travellers",
        ),
        correct_option_index=0,
        explanation="Young children carry most infection, and their carers are exposed repeatedly.",
    ),
    QuizQuestion(
        question_id="trachoma-5",
        condition=HealthCondition.TRACHOMA,
        prompt="What can repeated untreated trachoma cause?",
        options=(
            "Loss of sight over time",
            "A mild cough",
            "Stomach pain",
            "Nothing at all",
        ),
        correct_option_index=0,
        explanation="Repeated infection scars the eyelid and can eventually cause blindness.",
    ),
    QuizQuestion(
        question_id="schisto-4",
        condition=HealthCondition.SCHISTOSOMIASIS,
        prompt="Where should water be fetched from this season?",
        options=(
            "A pump or tap",
            "A still pond",
            "A slow stream",
            "A flooded field",
        ),
        correct_option_index=0,
        explanation="A pump or tap avoids the still fresh water where the host snails live.",
    ),
)

QUIZ_BANK = (
    *QUIZ_BANK,
    *EXTENDED_QUIZ_BANK,
    *TIERED_QUIZ_BANK,
    *SESSION_QUIZ_BANK,
    *DEPTH_QUIZ_BANK,
)


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
