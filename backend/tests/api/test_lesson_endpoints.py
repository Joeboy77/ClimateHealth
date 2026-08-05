import pytest
from fastapi.testclient import TestClient

from climahealth.domain.models import HealthCondition
from climahealth.services.citizens import GuardianTier
from climahealth.services.lessons import LESSONS_BY_KEY, lesson_for

HEAVY_RAIN = {"district_id": "madina", "scenario": "heavy_rain"}

# Tier 1, plus the two the engine raises most often alongside malaria in the wet season.
# Leaving those to the fallback would send most readers a placeholder.
WRITTEN = (
    HealthCondition.MALARIA,
    HealthCondition.CHOLERA,
    HealthCondition.MENINGITIS,
    HealthCondition.DIARRHOEAL_DISEASE,
    HealthCondition.RESPIRATORY_HEAT_ILLNESS,
    HealthCondition.SCHISTOSOMIASIS,
    HealthCondition.DENGUE,
)


def join(client: TestClient, age_band: str) -> dict[str, str]:
    token = client.post(
        "/citizens",
        json={"display_name": "Reader", "district_id": "madina", "age_band": age_band},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("condition", WRITTEN)
@pytest.mark.parametrize("tier", list(GuardianTier))
def test_every_covered_condition_is_written_for_every_age(
    condition: HealthCondition, tier: GuardianTier
):
    """A nine-year-old and a grandmother both need to know about standing water, and
    neither is served by the other's version."""
    assert (condition, tier) in LESSONS_BY_KEY


def test_a_condition_without_written_content_says_so_rather_than_borrowing_an_adults():
    written = lesson_for(HealthCondition.TRACHOMA, GuardianTier.ANANSI, "Wash faces daily")

    assert "still being written" in written.body
    assert written.action == "Wash faces daily"


def test_the_same_district_teaches_four_different_lessons_by_age(
    client: TestClient, national_headers: dict[str, str]
):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    titles = {
        band: client.get("/lessons/today/madina", headers=join(client, band)).json()["lesson"][
            "title"
        ]
        for band in ("6_12", "13_17", "18_34", "60_plus")
    }

    assert len(set(titles.values())) == 4


def test_the_lesson_follows_the_weather_not_a_syllabus(
    client: TestClient, national_headers: dict[str, str]
):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)
    wet = client.get("/lessons/today/madina", headers=join(client, "18_34")).json()

    client.post(
        "/demo/set-conditions",
        json={"district_id": "madina", "scenario": "dry_and_dusty"},
        headers=national_headers,
    )
    dry = client.get("/lessons/today/madina", headers=join(client, "18_34")).json()

    assert wet["triggered_by"] != dry["triggered_by"]


def test_a_child_gets_the_child_tier(client: TestClient, national_headers: dict[str, str]):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    body = client.get("/lessons/today/madina", headers=join(client, "6_12")).json()

    assert body["tier"] == "anansi"
    assert body["tier_name"] == "Anansi's Climate Tales"


def test_a_district_user_cannot_read_another_districts_lesson(
    client: TestClient, madina_headers: dict[str, str]
):
    assert client.get("/lessons/today/wa", headers=madina_headers).status_code == 403


def test_an_agency_account_without_a_guardian_record_gets_the_adult_lesson(
    client: TestClient, national_headers: dict[str, str]
):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    body = client.get("/lessons/today/madina", headers=national_headers).json()

    assert body["tier"] == "community_champion"


def test_the_quiz_is_asked_differently_of_a_child_and_an_elder(
    client: TestClient, national_headers: dict[str, str]
):
    """A question nobody understands teaches nothing, same as the lesson."""
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    child = client.get("/quiz/daily/madina", headers=join(client, "6_12")).json()
    elder = client.get("/quiz/daily/madina", headers=join(client, "60_plus")).json()

    assert child["prompt"] != elder["prompt"]
    assert child["question_id"].endswith("child-1")
    assert elder["question_id"].endswith("elder-1")


def test_an_age_without_its_own_question_still_gets_one(
    client: TestClient, national_headers: dict[str, str]
):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    adult = client.get("/quiz/daily/madina", headers=join(client, "18_34")).json()

    assert adult["prompt"]
    assert adult["options"]
