from fastapi.testclient import TestClient

REGISTRATION = {
    "display_name": "Ama Serwaa",
    "district_id": "madina",
    "age_band": "18_34",
    "language": "tw",
}


def test_age_bands_are_open_so_the_signup_screen_can_render_first(client: TestClient):
    response = client.get("/citizens/age-bands")

    assert response.status_code == 200
    bands = response.json()
    assert [band["age_band"] for band in bands] == [
        "6_12",
        "13_17",
        "18_34",
        "35_59",
        "60_plus",
    ]


def test_registering_needs_no_password_and_no_verification_code(client: TestClient):
    response = client.post("/citizens", json=REGISTRATION)

    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["citizen"]["display_name"] == "Ama Serwaa"
    assert body["citizen"]["language"] == "tw"


def test_the_age_band_decides_the_tier_not_a_separate_choice(client: TestClient):
    child = client.post("/citizens", json={**REGISTRATION, "age_band": "6_12"}).json()
    teen = client.post("/citizens", json={**REGISTRATION, "age_band": "13_17"}).json()
    elder = client.post("/citizens", json={**REGISTRATION, "age_band": "60_plus"}).json()

    assert child["citizen"]["tier"] == "anansi"
    assert teen["citizen"]["tier"] == "risk_scout"
    assert elder["citizen"]["tier"] == "voice_first"


def test_a_minor_is_never_offered_health_insurance_and_is_supervised(client: TestClient):
    """Proposal section 12.3: under-18s are already exempt from premiums, and health
    rewards for a child in exchange for fieldwork would be wrong."""
    for band in ("6_12", "13_17"):
        citizen = client.post("/citizens", json={**REGISTRATION, "age_band": band}).json()[
            "citizen"
        ]

        assert citizen["is_minor"] is True
        assert citizen["health_rewards_available"] is False
        assert citizen["supervised_missions_only"] is True


def test_an_adult_may_be_offered_the_health_dividend(client: TestClient):
    citizen = client.post("/citizens", json=REGISTRATION).json()["citizen"]

    assert citizen["is_minor"] is False
    assert citizen["health_rewards_available"] is True
    assert citizen["supervised_missions_only"] is False


def test_registering_into_a_district_that_does_not_exist_is_refused(client: TestClient):
    response = client.post("/citizens", json={**REGISTRATION, "district_id": "atlantis"})

    assert response.status_code == 404


def test_an_age_band_outside_the_offered_set_is_refused(client: TestClient):
    response = client.post("/citizens", json={**REGISTRATION, "age_band": "0_5"})

    assert response.status_code == 422


def test_a_registered_guardian_is_scoped_to_their_own_district(client: TestClient):
    token = client.post("/citizens", json=REGISTRATION).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/districts/madina", headers=headers).status_code == 200
    assert client.get("/districts/wa", headers=headers).status_code == 403


def test_a_guardian_can_read_their_own_record(client: TestClient):
    session = client.post("/citizens", json=REGISTRATION).json()
    headers = {"Authorization": f"Bearer {session['access_token']}"}

    response = client.get("/citizens/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["user_id"] == session["citizen"]["user_id"]


def test_a_citizen_may_not_broadcast_to_the_public(client: TestClient):
    """A responder role, so the coordinator-only rule already covers this."""
    token = client.post("/citizens", json=REGISTRATION).json()["access_token"]

    response = client.post(
        "/outreach/sms/madina",
        headers={"Authorization": f"Bearer {token}"},
        json={"recipients": ["233241234567"]},
    )

    assert response.status_code == 403


def test_joining_makes_you_a_guardian_in_one_step(client: TestClient):
    """Proposal section 11: everyone who joins becomes a Climate Guardian. Without the
    record, the first quiz answer has nowhere to put the points."""
    session = client.post("/citizens", json=REGISTRATION).json()
    headers = {"Authorization": f"Bearer {session['access_token']}"}

    profile = client.get(f"/guardian/{session['citizen']['user_id']}", headers=headers)

    assert profile.status_code == 200
    assert profile.json()["points"] == 0
    assert profile.json()["district_id"] == "madina"


def test_a_new_guardian_can_answer_the_daily_quiz(
    client: TestClient, national_headers: dict[str, str]
):
    client.post(
        "/demo/set-conditions",
        json={"district_id": "madina", "scenario": "heavy_rain"},
        headers=national_headers,
    )
    session = client.post("/citizens", json=REGISTRATION).json()
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    quiz = client.get("/quiz/daily/madina", headers=headers).json()

    result = client.post(
        "/quiz/answer",
        headers=headers,
        json={
            "user_id": session["citizen"]["user_id"],
            "question_id": quiz["question_id"],
            "selected_option_index": quiz.get("correct_option_index", 0),
        },
    )

    assert result.status_code == 200
    assert result.json()["points_awarded"] > 0
