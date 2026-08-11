from datetime import date, timedelta

from pydantic import Field

from climahealth.services.citizens import GuardianTier
from climahealth.services.models import ServiceModel

# Five questions is the floor for everybody: fewer than that and a run is over before it
# has taught anything. Pacing for older readers is carried by audio, larger type and no
# timer rather than by a shorter session.
MINIMUM_SESSION_LENGTH = 5
SESSION_LENGTH: dict[GuardianTier, int] = {
    GuardianTier.ANANSI: 6,
    GuardianTier.RISK_SCOUT: 6,
    GuardianTier.COMMUNITY_CHAMPION: 5,
    GuardianTier.VOICE_FIRST: 5,
}
DEFAULT_SESSION_LENGTH = MINIMUM_SESSION_LENGTH

CORRECT_POINTS = 20
ATTEMPT_POINTS = 5
PERFECT_SESSION_BONUS = 15

# One missed day a week is forgiven automatically. People miss days because of illness,
# travel, a dead battery, or the flood we just warned them about. A health application
# that punishes that is using guilt as a retention mechanic, which we will not do.
REST_DAYS_PER_WEEK = 1


class Streak(ServiceModel):
    """How many days running somebody has come back.

    Counted and celebrated, never used to shame. There are no hearts and no lock-out:
    getting a question wrong never withholds health information from anybody.
    """

    current_days: int = Field(ge=0)
    longest_days: int = Field(ge=0)
    last_active_on: date | None = None
    rest_days_used: int = Field(default=0, ge=0)

    @property
    def is_alive(self) -> bool:
        return self.current_days > 0


def session_length_for(tier: GuardianTier | None) -> int:
    if tier is None:
        return DEFAULT_SESSION_LENGTH
    return max(SESSION_LENGTH.get(tier, DEFAULT_SESSION_LENGTH), MINIMUM_SESSION_LENGTH)


def advance_streak(streak: Streak, today: date) -> Streak:
    """Move the streak on for a session completed today.

    A gap of one day is forgiven once a week rather than breaking the run outright.
    """
    last = streak.last_active_on
    if last == today:
        return streak

    if last is None:
        return streak.model_copy(
            update={
                "current_days": 1,
                "longest_days": max(streak.longest_days, 1),
                "last_active_on": today,
                "rest_days_used": 0,
            }
        )

    gap = (today - last).days
    fresh_week = (today - last).days >= 7
    rest_used = 0 if fresh_week else streak.rest_days_used

    if gap == 1:
        run = streak.current_days + 1
    elif gap == 2 and rest_used < REST_DAYS_PER_WEEK:
        # One forgiven day: the run continues and the rest day is spent.
        run = streak.current_days + 1
        rest_used += 1
    else:
        run = 1
        rest_used = 0

    return streak.model_copy(
        update={
            "current_days": run,
            "longest_days": max(streak.longest_days, run),
            "last_active_on": today,
            "rest_days_used": rest_used,
        }
    )


def streak_state_on(streak: Streak, today: date) -> Streak:
    """What the streak looks like today, before any session is completed.

    A run that has already lapsed shows as zero rather than as a number that is about to
    vanish without explanation.
    """
    last = streak.last_active_on
    if last is None:
        return streak
    gap = (today - last).days
    forgiven = gap == 2 and streak.rest_days_used < REST_DAYS_PER_WEEK
    if gap <= 1 or forgiven:
        return streak
    return streak.model_copy(update={"current_days": 0, "rest_days_used": 0})


def points_for(correct_count: int, total: int) -> int:
    """Attempting still earns something. The point is that people keep learning."""
    if total <= 0:
        return 0
    earned = correct_count * CORRECT_POINTS + (total - correct_count) * ATTEMPT_POINTS
    if correct_count == total:
        earned += PERFECT_SESSION_BONUS
    return earned


def next_reset(today: date) -> date:
    return today + timedelta(days=1)


class AnsweredQuestion(ServiceModel):
    question_id: str
    correct: bool
    correct_option_index: int
    explanation: str


class SessionAnswer(ServiceModel):
    question_id: str
    selected_option_index: int = Field(ge=0)


class SessionSubmission(ServiceModel):
    user_id: str
    answers: tuple[SessionAnswer, ...] = Field(min_length=1, max_length=10)


class SessionResult(ServiceModel):
    correct_count: int = Field(ge=0)
    total: int = Field(ge=0)
    points_awarded: int = Field(ge=0)
    total_points: int = Field(ge=0)
    streak: Streak
    perfect: bool
    answers: tuple[AnsweredQuestion, ...]
