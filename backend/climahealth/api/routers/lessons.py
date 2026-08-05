from fastapi import APIRouter

from climahealth.api.dependencies import ContainerDependency, CurrentUser, PermittedDistrict
from climahealth.api.schemas.common import ApiModel
from climahealth.services.citizens import TIER_NAMES, GuardianTier
from climahealth.services.lessons import Lesson, lesson_for
from climahealth.services.narration import NarrationLanguage
from climahealth.services.sms_alerts import ACTION_WORDS

router = APIRouter(tags=["lessons"])


class TodaysLesson(ApiModel):
    """The lesson the weather asked for, written for the reader's age."""

    district_id: str
    district_name: str
    tier: GuardianTier
    tier_name: str
    lesson: Lesson
    triggered_by: str


@router.get("/lessons/today/{district_id}", response_model=TodaysLesson)
def get_todays_lesson(
    district: PermittedDistrict, user: CurrentUser, container: ContainerDependency
) -> TodaysLesson:
    """Today's lesson for this district, pitched at the caller's age band.

    Triggered by the weather rather than a syllabus, per proposal section 11.1: the
    lesson about standing water arrives the week the rain does, which is the only week
    anybody will act on it.
    """
    report = container.risk_service.report_for(district)
    leading = report.risks[0]

    citizen = container.citizen_service.find(user.user_id)
    tier = citizen.tier if citizen is not None else GuardianTier.COMMUNITY_CHAMPION

    action = ACTION_WORDS[NarrationLanguage.ENGLISH][leading.condition]

    return TodaysLesson(
        district_id=district.district_id,
        district_name=district.name,
        tier=tier,
        tier_name=TIER_NAMES[tier],
        lesson=lesson_for(leading.condition, tier, action),
        triggered_by=leading.condition.value,
    )
