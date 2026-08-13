from datetime import date

from fastapi import APIRouter, HTTPException, status

from climahealth.api.dependencies import ContainerDependency, CurrentUser, PermittedDistrict
from climahealth.api.schemas.common import ApiModel
from climahealth.domain.models import HealthCondition, RiskLevel
from climahealth.services.citizens import GuardianTier
from climahealth.services.gamification_service import GuardianNotFound, QuizQuestion
from climahealth.services.quiz_session import (
    SessionResult,
    SessionSubmission,
    Streak,
    session_length_for,
    streak_state_on,
)
from climahealth.services.rewards import (
    NhisRenewal,
    RedemptionRefused,
    RenewalQuote,
    quote_for,
)

router = APIRouter(tags=["play"])


class SessionQuestion(ApiModel):
    """A question, with its answer.

    The answer travels with the question so the phone can react the instant somebody
    chooses, and so a run still works with no signal. Scoring stays on the server, so a
    tampered client cannot award itself points: it sends the indices it chose and the
    server decides what they were worth.
    """

    question_id: str
    prompt: str
    options: list[str]
    correct_option_index: int
    explanation: str


class QuizSessionResponse(ApiModel):
    """A short run of questions about the hazard the engine raised here today."""

    district_id: str
    district_name: str
    condition: HealthCondition
    level: RiskLevel
    tier: GuardianTier
    quiz_date: date
    questions: list[SessionQuestion]
    streak: Streak


def _as_session_question(question: QuizQuestion) -> SessionQuestion:
    return SessionQuestion(
        question_id=question.question_id,
        prompt=question.prompt,
        options=list(question.options),
        correct_option_index=question.correct_option_index,
        explanation=question.explanation,
    )


@router.get("/play/session/{district_id}", response_model=QuizSessionResponse)
def get_session(
    district: PermittedDistrict, user: CurrentUser, container: ContainerDependency
) -> QuizSessionResponse:
    """Today's run of questions, sized and worded for the reader's age band."""
    report = container.risk_service.report_for(district)
    leading = report.risks[0]

    citizen = container.citizen_service.find(user.user_id)
    tier = citizen.tier if citizen is not None else GuardianTier.COMMUNITY_CHAMPION

    questions = container.quizzes.session_for(
        leading.condition, report.generated_on, tier, session_length_for(tier)
    )
    guardian = container.guardians.find(user.user_id)
    streak = streak_state_on(
        guardian.streak if guardian is not None else Streak(current_days=0, longest_days=0),
        report.generated_on,
    )

    return QuizSessionResponse(
        district_id=district.district_id,
        district_name=district.name,
        condition=leading.condition,
        level=leading.level,
        tier=tier,
        quiz_date=report.generated_on,
        questions=[_as_session_question(question) for question in questions],
        streak=streak,
    )


@router.post("/play/session", response_model=SessionResult)
def submit_session(
    submission: SessionSubmission, user: CurrentUser, container: ContainerDependency
) -> SessionResult:
    """Score a completed run.

    Every answer earns something. There are no hearts and no lock-out: getting a question
    wrong never withholds health information from anybody.
    """
    _ = user
    try:
        return container.gamification_service.score_session(user, submission)
    except GuardianNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/rewards/quote/{user_id}", response_model=RenewalQuote)
def get_quote(user_id: str, user: CurrentUser, container: ContainerDependency) -> RenewalQuote:
    """How close this Guardian is to a year of NHIS cover."""
    guardian = container.gamification_service.resolve(user, user_id)
    citizen = container.citizen_service.find(guardian.user_id)
    if citizen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This account is not a registered Guardian",
        )
    return quote_for(guardian.points, citizen.age_band)


class RenewalRequest(ApiModel):
    user_id: str


@router.post("/rewards/redeem", response_model=NhisRenewal)
def redeem(
    request: RenewalRequest, user: CurrentUser, container: ContainerDependency
) -> NhisRenewal:
    """Claim a year of NHIS cover with earned points.

    This records a claim; it does not renew anything. Ghana Health Service does the
    renewal and confirms it, because the platform cannot issue cover on a government
    scheme's behalf and should not say that it has.
    """
    try:
        return container.rewards_service.redeem(user, request.user_id)
    except RedemptionRefused as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except GuardianNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
