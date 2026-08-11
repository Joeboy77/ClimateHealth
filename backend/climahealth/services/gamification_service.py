from datetime import date
from enum import StrEnum

from pydantic import Field

from climahealth.domain.models import HealthCondition, RiskLevel
from climahealth.services.access import AuthenticatedUser, DistrictAccessDenied
from climahealth.services.citizens import GuardianTier
from climahealth.services.models import District, ServiceModel
from climahealth.services.ports import (
    Clock,
    GuardianStore,
    QuizRepository,
    ReportStore,
)
from climahealth.services.quiz_session import (
    AnsweredQuestion,
    SessionResult,
    SessionSubmission,
    Streak,
    advance_streak,
    points_for,
    streak_state_on,
)
from climahealth.services.risk_service import RiskService

QUIZ_CORRECT_POINTS = 20
QUIZ_PARTICIPATION_POINTS = 5

SHIELD_BASE_STRENGTH = 20
POINTS_PER_ACTIVE_GUARDIAN = 5
POINTS_PER_COMPLETED_MISSION = 3
POINTS_PER_COMMUNITY_REPORT = 4
MAXIMUM_SHIELD_STRENGTH = 100

SHIELD_STRONG_THRESHOLD = 70
SHIELD_HOLDING_THRESHOLD = 40


class ShieldStatus(StrEnum):
    STRONG = "strong"
    HOLDING = "holding"
    WEAK = "weak"


class GuardianLevel(ServiceModel):
    name: str
    minimum_points: int = Field(ge=0)
    unlocks: str


class Guardian(ServiceModel):
    user_id: str
    display_name: str
    district_id: str
    points: int = Field(ge=0)
    streak: Streak = Streak(current_days=0, longest_days=0)
    completed_mission_ids: tuple[str, ...] = ()
    answered_question_ids: tuple[str, ...] = ()


class GuardianProfile(ServiceModel):
    user_id: str
    display_name: str
    district_id: str
    points: int
    level: GuardianLevel
    missions_completed: int
    streak: Streak


class RewardLadder(ServiceModel):
    user_id: str
    points: int
    current_level: GuardianLevel
    next_level: GuardianLevel | None
    points_to_next_level: int
    ladder: tuple[GuardianLevel, ...]


class QuizQuestion(ServiceModel):
    question_id: str
    condition: HealthCondition
    # None means the question suits any age. A tiered question is preferred over it when
    # one exists, so a child is never asked an adult's wording.
    tier: "GuardianTier | None" = None
    prompt: str
    options: tuple[str, ...]
    correct_option_index: int = Field(ge=0)
    explanation: str


class DailyQuiz(ServiceModel):
    district_id: str
    district_name: str
    quiz_date: date
    hazard_condition: HealthCondition
    hazard_level: RiskLevel
    question_id: str
    prompt: str
    options: tuple[str, ...]


class QuizAnswer(ServiceModel):
    user_id: str
    question_id: str
    selected_option_index: int = Field(ge=0)


class QuizResult(ServiceModel):
    correct: bool
    correct_option_index: int
    explanation: str
    points_awarded: int
    total_points: int


class MissionCompletion(ServiceModel):
    user_id: str
    mission_id: str


class Mission(ServiceModel):
    mission_id: str
    description: str
    points: int = Field(ge=0)


class MissionResult(ServiceModel):
    mission_id: str
    description: str
    points_awarded: int
    total_points: int


class DistrictShield(ServiceModel):
    district_id: str
    district_name: str
    status: ShieldStatus
    strength: int = Field(ge=0, le=MAXIMUM_SHIELD_STRENGTH)
    active_guardians: int = Field(ge=0)
    missions_completed: int = Field(ge=0)
    community_reports: int = Field(ge=0)
    outbreaks_averted: int = Field(ge=0)


class GuardianNotFound(LookupError):
    pass


class QuizQuestionNotFound(LookupError):
    pass


class UnknownMission(LookupError):
    pass


class MissionAlreadyCompleted(RuntimeError):
    pass


def level_for_points(points: int, ladder: tuple[GuardianLevel, ...]) -> GuardianLevel:
    reached = [level for level in ladder if points >= level.minimum_points]
    return reached[-1] if reached else ladder[0]


def next_level_after(
    current: GuardianLevel, ladder: tuple[GuardianLevel, ...]
) -> GuardianLevel | None:
    remaining = [level for level in ladder if level.minimum_points > current.minimum_points]
    return remaining[0] if remaining else None


def shield_status_for(strength: int) -> ShieldStatus:
    if strength >= SHIELD_STRONG_THRESHOLD:
        return ShieldStatus.STRONG
    if strength >= SHIELD_HOLDING_THRESHOLD:
        return ShieldStatus.HOLDING
    return ShieldStatus.WEAK


def shield_strength_for(
    active_guardians: int, missions_completed: int, community_reports: int
) -> int:
    raw = (
        SHIELD_BASE_STRENGTH
        + active_guardians * POINTS_PER_ACTIVE_GUARDIAN
        + missions_completed * POINTS_PER_COMPLETED_MISSION
        + community_reports * POINTS_PER_COMMUNITY_REPORT
    )
    return min(raw, MAXIMUM_SHIELD_STRENGTH)


class GamificationService:
    def __init__(
        self,
        guardians: GuardianStore,
        quizzes: QuizRepository,
        reports: ReportStore,
        risk_service: RiskService,
        clock: Clock,
    ) -> None:
        self._guardians = guardians
        self._quizzes = quizzes
        self._reports = reports
        self._risk_service = risk_service
        self._clock = clock

    def profile_for(self, user: AuthenticatedUser, user_id: str) -> GuardianProfile:
        guardian = self._resolve_guardian(user, user_id)
        return GuardianProfile(
            user_id=guardian.user_id,
            display_name=guardian.display_name,
            district_id=guardian.district_id,
            points=guardian.points,
            level=level_for_points(guardian.points, self._guardians.ladder()),
            missions_completed=len(guardian.completed_mission_ids),
            streak=streak_state_on(guardian.streak, self._clock.today()),
        )

    def rewards_for(self, user: AuthenticatedUser, user_id: str) -> RewardLadder:
        guardian = self._resolve_guardian(user, user_id)
        ladder = self._guardians.ladder()
        current = level_for_points(guardian.points, ladder)
        following = next_level_after(current, ladder)
        return RewardLadder(
            user_id=guardian.user_id,
            points=guardian.points,
            current_level=current,
            next_level=following,
            points_to_next_level=(following.minimum_points - guardian.points if following else 0),
            ladder=ladder,
        )

    def daily_quiz(self, district: District, tier: "GuardianTier | None" = None) -> DailyQuiz:
        report = self._risk_service.report_for(district)
        leading = report.risks[0]
        question = self._quizzes.question_for(leading.condition, report.generated_on, tier)
        return DailyQuiz(
            district_id=district.district_id,
            district_name=district.name,
            quiz_date=report.generated_on,
            hazard_condition=leading.condition,
            hazard_level=leading.level,
            question_id=question.question_id,
            prompt=question.prompt,
            options=question.options,
        )

    def answer_quiz(self, user: AuthenticatedUser, answer: QuizAnswer) -> QuizResult:
        guardian = self._resolve_guardian(user, answer.user_id)
        question = self._quizzes.find(answer.question_id)
        if question is None:
            raise QuizQuestionNotFound(f"Unknown question '{answer.question_id}'")

        correct = answer.selected_option_index == question.correct_option_index
        already_answered = question.question_id in guardian.answered_question_ids
        points = (
            0
            if already_answered
            else (QUIZ_CORRECT_POINTS if correct else QUIZ_PARTICIPATION_POINTS)
        )

        updated = self._guardians.record_quiz_answer(guardian.user_id, question.question_id, points)
        return QuizResult(
            correct=correct,
            correct_option_index=question.correct_option_index,
            explanation=question.explanation,
            points_awarded=points,
            total_points=updated.points,
        )

    def complete_mission(
        self, user: AuthenticatedUser, completion: MissionCompletion
    ) -> MissionResult:
        guardian = self._resolve_guardian(user, completion.user_id)
        mission = self._guardians.find_mission(completion.mission_id)
        if mission is None:
            raise UnknownMission(f"Unknown mission '{completion.mission_id}'")
        if mission.mission_id in guardian.completed_mission_ids:
            raise MissionAlreadyCompleted(
                f"Mission '{mission.mission_id}' has already been completed"
            )

        updated = self._guardians.record_mission(guardian.user_id, mission)
        return MissionResult(
            mission_id=mission.mission_id,
            description=mission.description,
            points_awarded=mission.points,
            total_points=updated.points,
        )

    def resolve(self, user: AuthenticatedUser, user_id: str) -> Guardian:
        return self._resolve_guardian(user, user_id)

    def spend(self, user_id: str, points: int) -> Guardian:
        return self._guardians.spend_points(user_id, points)

    def score_session(
        self, user: AuthenticatedUser, submission: SessionSubmission
    ) -> SessionResult:
        """Score a completed run of questions.

        Every answer earns something, because the aim is that people keep learning rather
        than that they perform. A question already answered on a previous day still shows
        its explanation but earns nothing, so the bank cannot be farmed.
        """
        guardian = self._resolve_guardian(user, submission.user_id)
        today = self._clock.today()

        answered: list[AnsweredQuestion] = []
        correct_count = 0
        fresh_ids: list[str] = []

        for entry in submission.answers:
            question = self._quizzes.find(entry.question_id)
            if question is None:
                raise QuizQuestionNotFound(f"Unknown question '{entry.question_id}'")

            correct = entry.selected_option_index == question.correct_option_index
            correct_count += int(correct)
            if question.question_id not in guardian.answered_question_ids:
                fresh_ids.append(question.question_id)

            answered.append(
                AnsweredQuestion(
                    question_id=question.question_id,
                    correct=correct,
                    correct_option_index=question.correct_option_index,
                    explanation=question.explanation,
                )
            )

        total = len(answered)
        scored_correct = min(correct_count, len(fresh_ids))
        points = points_for(scored_correct, len(fresh_ids)) if fresh_ids else 0
        streak = advance_streak(guardian.streak, today)
        updated = self._guardians.record_session(guardian.user_id, tuple(fresh_ids), points, streak)

        return SessionResult(
            correct_count=correct_count,
            total=total,
            points_awarded=points,
            total_points=updated.points,
            streak=updated.streak,
            perfect=correct_count == total and total > 0,
            answers=tuple(answered),
        )

    def shield_for(self, district: District) -> DistrictShield:
        guardians = self._guardians.for_district(district.district_id)
        missions_completed = sum(len(item.completed_mission_ids) for item in guardians)
        community_reports = len(self._reports.for_district(district.district_id))
        strength = shield_strength_for(len(guardians), missions_completed, community_reports)
        return DistrictShield(
            district_id=district.district_id,
            district_name=district.name,
            status=shield_status_for(strength),
            strength=strength,
            active_guardians=len(guardians),
            missions_completed=missions_completed,
            community_reports=community_reports,
            outbreaks_averted=self._guardians.outbreaks_averted(district.district_id),
        )

    def _resolve_guardian(self, user: AuthenticatedUser, user_id: str) -> Guardian:
        guardian = self._guardians.find(user_id)
        if guardian is None:
            guardian = self._enrol_on_first_use(user, user_id)
        if guardian is None:
            raise GuardianNotFound(f"Unknown guardian '{user_id}'")
        if user.user_id != guardian.user_id and not user.scope.permits(guardian.district_id):
            raise DistrictAccessDenied(guardian.district_id)
        return guardian

    def _enrol_on_first_use(self, user: AuthenticatedUser, user_id: str) -> Guardian | None:
        """Enrol a signed-in citizen who somehow has no Guardian record.

        Everyone who joins Dawuro is enrolled at registration, but accounts created
        before that existed have no record, and a missing one used to end a finished
        quiz in a 404 with the answers already given. Nobody should lose a completed
        run to a gap in their own account.

        Only the account holder is created this way, and only from claims already in
        their token, so this cannot mint a Guardian for anybody else.
        """
        if user_id != user.user_id or user.scope.district_id is None:
            return None
        return self._guardians.enrol(user.user_id, user.display_name, user.scope.district_id)
