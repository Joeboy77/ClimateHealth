import pytest

HEAVY_RAIN = {"district_id": "madina", "scenario": "heavy_rain"}
DRY_AND_DUSTY = {"district_id": "wa", "scenario": "dry_and_dusty"}

PROTECTED_ROUTES = (
    "/guardian/user-madina",
    "/rewards/user-madina",
    "/quiz/daily/madina",
    "/shield/madina",
)


@pytest.mark.parametrize("route", PROTECTED_ROUTES)
def test_gamification_routes_require_authentication(client, route):
    assert client.get(route).status_code == 401


def test_a_guardian_profile_carries_points_level_and_district(client, madina_headers):
    body = client.get("/guardian/user-madina", headers=madina_headers).json()

    assert body["user_id"] == "user-madina"
    assert body["district_id"] == "madina"
    assert body["points"] == 340
    assert body["level"]["name"] == "Defender"
    assert body["missions_completed"] == 2


def test_an_unknown_guardian_is_not_found(client, national_headers):
    assert client.get("/guardian/nobody", headers=national_headers).status_code == 404


def test_a_district_user_cannot_read_a_guardian_from_another_district(client, madina_headers):
    assert client.get("/guardian/citizen-1120", headers=madina_headers).status_code == 403


def test_a_user_can_always_read_their_own_profile(client, madina_headers):
    assert client.get("/guardian/user-madina", headers=madina_headers).status_code == 200


def test_the_reward_ladder_shows_the_next_unlock(client, madina_headers):
    body = client.get("/rewards/user-madina", headers=madina_headers).json()

    assert body["current_level"]["name"] == "Defender"
    assert body["next_level"]["name"] == "Guardian"
    assert body["points_to_next_level"] == 360
    assert body["next_level"]["unlocks"]
    assert len(body["ladder"]) == 5


def test_the_top_of_the_ladder_has_no_next_level(client, national_headers):
    body = client.get("/rewards/user-national", headers=national_headers).json()

    assert body["current_level"]["name"] == "Guardian"
    assert body["next_level"]["name"] == "Champion"


def test_the_daily_quiz_follows_the_districts_leading_hazard(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    body = client.get("/quiz/daily/madina", headers=national_headers).json()

    assert body["hazard_level"] in {"high", "severe"}
    assert body["question_id"].startswith(body["hazard_condition"].split("_")[0])
    assert len(body["options"]) == 4


def test_the_quiz_changes_when_the_hazard_changes(client, national_headers):
    client.post("/demo/set-conditions", json=DRY_AND_DUSTY, headers=national_headers)

    body = client.get("/quiz/daily/wa", headers=national_headers).json()

    assert body["hazard_condition"] in {
        "meningitis",
        "lassa_fever",
        "trachoma",
        "air_pollution_cardiorespiratory",
    }
    assert body["question_id"].startswith(body["hazard_condition"])


def test_the_quiz_never_leaks_the_answer(client, national_headers):
    body = client.get("/quiz/daily/madina", headers=national_headers).json()

    assert "correct_option_index" not in body
    assert "explanation" not in body


def test_a_district_user_cannot_take_another_districts_quiz(client, madina_headers):
    assert client.get("/quiz/daily/wa", headers=madina_headers).status_code == 403


def test_a_correct_answer_awards_points_and_explains_why(client, madina_headers):
    response = client.post(
        "/quiz/answer",
        json={"user_id": "user-madina", "question_id": "malaria-1", "selected_option_index": 0},
        headers=madina_headers,
    )

    body = response.json()
    assert body["correct"] is True
    assert body["points_awarded"] == 20
    assert body["total_points"] == 360
    assert "standing water" in body["explanation"].lower()


def test_a_wrong_answer_still_teaches_and_gives_participation_points(client, madina_headers):
    body = client.post(
        "/quiz/answer",
        json={"user_id": "user-madina", "question_id": "malaria-1", "selected_option_index": 2},
        headers=madina_headers,
    ).json()

    assert body["correct"] is False
    assert body["points_awarded"] == 5
    assert body["correct_option_index"] == 0
    assert body["explanation"]


def test_the_same_question_cannot_be_farmed_for_points(client, madina_headers):
    answer = {
        "user_id": "user-madina",
        "question_id": "malaria-1",
        "selected_option_index": 0,
    }
    client.post("/quiz/answer", json=answer, headers=madina_headers)

    second = client.post("/quiz/answer", json=answer, headers=madina_headers).json()

    assert second["points_awarded"] == 0
    assert second["total_points"] == 360


def test_answering_an_unknown_question_is_not_found(client, madina_headers):
    response = client.post(
        "/quiz/answer",
        json={"user_id": "user-madina", "question_id": "nope", "selected_option_index": 0},
        headers=madina_headers,
    )

    assert response.status_code == 404


def test_a_completed_mission_awards_its_points(client, madina_headers):
    body = client.post(
        "/guardian/mission",
        json={"user_id": "user-madina", "mission_id": "treat-drinking-water"},
        headers=madina_headers,
    ).json()

    assert body["points_awarded"] == 20
    assert body["total_points"] == 360
    assert body["description"]


def test_a_mission_cannot_be_completed_twice(client, madina_headers):
    response = client.post(
        "/guardian/mission",
        json={"user_id": "user-madina", "mission_id": "clear-standing-water"},
        headers=madina_headers,
    )

    assert response.status_code == 409


def test_an_unknown_mission_is_not_found(client, madina_headers):
    response = client.post(
        "/guardian/mission",
        json={"user_id": "user-madina", "mission_id": "fly-to-mars"},
        headers=madina_headers,
    )

    assert response.status_code == 404


def test_a_mission_raises_the_profile_points(client, madina_headers):
    client.post(
        "/guardian/mission",
        json={"user_id": "user-madina", "mission_id": "report-a-hazard"},
        headers=madina_headers,
    )

    profile = client.get("/guardian/user-madina", headers=madina_headers).json()

    assert profile["points"] == 380
    assert profile["missions_completed"] == 3


def test_enough_points_promote_a_guardian_to_the_next_level(client, madina_headers):
    for mission_id in ("treat-drinking-water", "hang-treated-net", "report-a-hazard"):
        client.post(
            "/guardian/mission",
            json={"user_id": "user-madina", "mission_id": mission_id},
            headers=madina_headers,
        )

    profile = client.get("/guardian/user-madina", headers=madina_headers).json()

    assert profile["points"] == 425
    assert profile["level"]["name"] == "Defender"


def test_the_shield_reports_status_strength_and_averted_outbreaks(client, madina_headers):
    body = client.get("/shield/madina", headers=madina_headers).json()

    assert body["district_id"] == "madina"
    assert body["status"] in {"strong", "holding", "weak"}
    assert 0 <= body["strength"] <= 100
    assert body["active_guardians"] == 3
    assert body["outbreaks_averted"] == 3
    assert body["community_reports"] >= 2


def test_completing_a_mission_strengthens_the_district_shield(client, madina_headers):
    before = client.get("/shield/madina", headers=madina_headers).json()["strength"]

    client.post(
        "/guardian/mission",
        json={"user_id": "user-madina", "mission_id": "treat-drinking-water"},
        headers=madina_headers,
    )
    after = client.get("/shield/madina", headers=madina_headers).json()["strength"]

    assert after > before


def test_a_district_user_cannot_read_another_districts_shield(client, madina_headers):
    assert client.get("/shield/wa", headers=madina_headers).status_code == 403
