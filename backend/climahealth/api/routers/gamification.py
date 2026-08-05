from fastapi import APIRouter, HTTPException, status

from climahealth.api.dependencies import ContainerDependency, CurrentUser, PermittedDistrict
from climahealth.services.gamification_service import (
    DailyQuiz,
    DistrictShield,
    GuardianNotFound,
    GuardianProfile,
    MissionAlreadyCompleted,
    MissionCompletion,
    MissionResult,
    QuizAnswer,
    QuizQuestionNotFound,
    QuizResult,
    RewardLadder,
    UnknownMission,
)

router = APIRouter(tags=["gamification"])


@router.get("/guardian/{user_id}", response_model=GuardianProfile)
def get_guardian(
    user_id: str, user: CurrentUser, container: ContainerDependency
) -> GuardianProfile:
    """Return a Climate Guardian's points, level and district."""
    try:
        return container.gamification_service.profile_for(user, user_id)
    except GuardianNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/rewards/{user_id}", response_model=RewardLadder)
def get_rewards(user_id: str, user: CurrentUser, container: ContainerDependency) -> RewardLadder:
    """Return reward ladder status and what the next level unlocks."""
    try:
        return container.gamification_service.rewards_for(user, user_id)
    except GuardianNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/quiz/daily/{district_id}", response_model=DailyQuiz)
def get_daily_quiz(
    district: PermittedDistrict, user: CurrentUser, container: ContainerDependency
) -> DailyQuiz:
    """Today's quiz, tied to the district's leading hazard and written for the reader.

    The same hazard is asked differently of a child and of an elder, for the same reason
    the lesson is written differently: a question nobody understands teaches nothing.
    """
    citizen = container.citizen_service.find(user.user_id)
    return container.gamification_service.daily_quiz(
        district, citizen.tier if citizen is not None else None
    )


@router.post("/quiz/answer", response_model=QuizResult)
def answer_quiz(
    answer: QuizAnswer, user: CurrentUser, container: ContainerDependency
) -> QuizResult:
    """Submit a quiz answer and return points and the correct explanation."""
    try:
        return container.gamification_service.answer_quiz(user, answer)
    except (GuardianNotFound, QuizQuestionNotFound) as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/guardian/mission", response_model=MissionResult)
def complete_mission(
    completion: MissionCompletion, user: CurrentUser, container: ContainerDependency
) -> MissionResult:
    """Record a completed mission and award its points."""
    try:
        return container.gamification_service.complete_mission(user, completion)
    except (GuardianNotFound, UnknownMission) as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except MissionAlreadyCompleted as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/shield/{district_id}", response_model=DistrictShield)
def get_shield(district: PermittedDistrict, container: ContainerDependency) -> DistrictShield:
    """Return a district's shield status and outbreak-averted count."""
    return container.gamification_service.shield_for(district)
