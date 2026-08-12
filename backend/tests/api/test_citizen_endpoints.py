from itertools import count

from fastapi.testclient import TestClient

_NUMBERS = count(1)

BASE_REGISTRATION = {
    "display_name": "Ama Serwaa",
    "district_id": "madina",
    "age_band": "18_34",
    "language": "tw",
    "password": "keep-well",
}


def registration(**overrides: object) -> dict[str, object]:
    """A fresh registration. Every account needs its own number, so the number is
    issued here rather than shared, and a test that registers twice gets two people."""
    return {
        **BASE_REGISTRATION,
        "phone_number": f"024{next(_NUMBERS):07d}",
        **overrides,
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


def test_registering_needs_no_verification_code(client: TestClient):
    response = client.post("/citizens", json=registration())

    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["citizen"]["display_name"] == "Ama Serwaa"
    assert body["citizen"]["language"] == "tw"


def test_the_age_band_decides_the_tier_not_a_separate_choice(client: TestClient):
    child = client.post("/citizens", json=registration(age_band="6_12")).json()
    teen = client.post("/citizens", json=registration(age_band="13_17")).json()
    elder = client.post("/citizens", json=registration(age_band="60_plus")).json()

    assert child["citizen"]["tier"] == "anansi"
    assert teen["citizen"]["tier"] == "risk_scout"
    assert elder["citizen"]["tier"] == "voice_first"


def test_a_minor_is_never_offered_health_insurance_and_is_supervised(client: TestClient):
    """Proposal section 12.3: under-18s are already exempt from premiums, and health
    rewards for a child in exchange for fieldwork would be wrong."""
    for band in ("6_12", "13_17"):
        citizen = client.post("/citizens", json=registration(age_band=band)).json()["citizen"]

        assert citizen["is_minor"] is True
        assert citizen["health_rewards_available"] is False
        assert citizen["supervised_missions_only"] is True


def test_an_adult_may_be_offered_the_health_dividend(client: TestClient):
    citizen = client.post("/citizens", json=registration()).json()["citizen"]

    assert citizen["is_minor"] is False
    assert citizen["health_rewards_available"] is True
    assert citizen["supervised_missions_only"] is False


def test_registering_into_a_district_that_does_not_exist_is_refused(client: TestClient):
    response = client.post("/citizens", json=registration(district_id="atlantis"))

    assert response.status_code == 404


def test_an_age_band_outside_the_offered_set_is_refused(client: TestClient):
    response = client.post("/citizens", json=registration(age_band="0_5"))

    assert response.status_code == 422


def test_a_registered_guardian_is_scoped_to_their_own_district(client: TestClient):
    token = client.post("/citizens", json=registration()).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/districts/madina", headers=headers).status_code == 200
    assert client.get("/districts/wa", headers=headers).status_code == 403


def test_a_guardian_can_read_their_own_record(client: TestClient):
    session = client.post("/citizens", json=registration()).json()
    headers = {"Authorization": f"Bearer {session['access_token']}"}

    response = client.get("/citizens/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["user_id"] == session["citizen"]["user_id"]


def test_a_citizen_may_not_broadcast_to_the_public(client: TestClient):
    """A responder role, so the coordinator-only rule already covers this."""
    token = client.post("/citizens", json=registration()).json()["access_token"]

    response = client.post(
        "/outreach/sms/madina",
        headers={"Authorization": f"Bearer {token}"},
        json={"recipients": ["233241234567"]},
    )

    assert response.status_code == 403


def test_joining_makes_you_a_guardian_in_one_step(client: TestClient):
    """Proposal section 11: everyone who joins becomes a Climate Guardian. Without the
    record, the first quiz answer has nowhere to put the points."""
    session = client.post("/citizens", json=registration()).json()
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
    session = client.post("/citizens", json=registration()).json()
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


def finish_a_run(client: TestClient, token: str, user_id: str):
    session = client.get(
        "/play/session/madina", headers={"authorization": f"Bearer {token}"}
    ).json()
    answers = [
        {"question_id": question["question_id"], "selected_option_index": 0}
        for question in session["questions"]
    ]
    return client.post(
        "/play/session",
        headers={"authorization": f"Bearer {token}"},
        json={"user_id": user_id, "answers": answers},
    )


def test_a_citizen_without_a_guardian_record_can_still_finish_a_run(client: TestClient, container):
    """Accounts made before enrolment existed at registration have no Guardian row,
    and a finished quiz used to 404 with the answers already given. Nobody should
    lose a completed run to a gap in their own account."""
    registered = client.post("/citizens", json=registration()).json()
    user_id = registered["citizen"]["user_id"]
    container.guardians._guardians.pop(user_id)

    response = finish_a_run(client, registered["access_token"], user_id)

    assert response.status_code == 200
    assert response.json()["total"] > 0


def test_one_citizen_cannot_mint_a_guardian_for_another_account(client: TestClient):
    registered = client.post("/citizens", json=registration()).json()

    response = finish_a_run(client, registered["access_token"], "somebody-else")

    assert response.status_code == 404


def test_the_guardian_card_carries_the_streak_so_the_home_screen_needs_one_call(
    client: TestClient,
):
    registered = client.post("/citizens", json=registration()).json()
    token, user_id = registered["access_token"], registered["citizen"]["user_id"]
    headers = {"authorization": f"Bearer {token}"}

    before = client.get(f"/guardian/{user_id}", headers=headers).json()
    assert before["points"] == 0
    assert before["streak"]["current_days"] == 0

    finish_a_run(client, token, user_id)

    after = client.get(f"/guardian/{user_id}", headers=headers).json()
    assert after["points"] > 0
    assert after["streak"]["current_days"] == 1


def test_signing_in_again_with_the_phone_number_and_password(client: TestClient):
    joining = registration()
    registered = client.post("/citizens", json=joining).json()

    signed_in = client.post(
        "/citizens/login",
        json={"phone_number": joining["phone_number"], "password": joining["password"]},
    )

    assert signed_in.status_code == 200
    assert signed_in.json()["citizen"]["user_id"] == registered["citizen"]["user_id"]


def test_the_number_is_recognised_however_it_was_typed(client: TestClient):
    """People write their number with the country code, a plus, or spaces from a contact
    card. All of those are the same person."""
    joining = registration(phone_number="0241234567")
    client.post("/citizens", json=joining)

    for written in ("+233 24 123 4567", "233241234567", "024 123 4567"):
        signed_in = client.post(
            "/citizens/login",
            json={"phone_number": written, "password": joining["password"]},
        )
        assert signed_in.status_code == 200, written


def test_a_wrong_password_and_an_unknown_number_are_refused_alike(client: TestClient):
    """Saying which half was wrong tells a stranger whether a number has an account."""
    joining = registration()
    client.post("/citizens", json=joining)

    wrong_password = client.post(
        "/citizens/login",
        json={"phone_number": joining["phone_number"], "password": "not-it"},
    )
    unknown_number = client.post(
        "/citizens/login", json={"phone_number": "0209999999", "password": "not-it"}
    )

    assert wrong_password.status_code == 401
    assert unknown_number.status_code == 401
    assert wrong_password.json()["detail"] == unknown_number.json()["detail"]


def test_one_number_cannot_hold_two_accounts(client: TestClient):
    joining = registration()
    client.post("/citizens", json=joining)

    again = client.post("/citizens", json=registration(phone_number=joining["phone_number"]))

    assert again.status_code == 409


def test_a_number_that_could_never_receive_an_sms_is_refused(client: TestClient):
    response = client.post("/citizens", json=registration(phone_number="0129999999"))

    assert response.status_code == 422


def test_a_password_is_required_to_register(client: TestClient):
    incomplete = registration()
    del incomplete["password"]

    assert client.post("/citizens", json=incomplete).status_code == 422


def test_neither_the_password_nor_the_number_ever_comes_back_in_a_response(
    client: TestClient,
):
    joining = registration()
    body = client.post("/citizens", json=joining).json()

    rendered = str(body)
    assert joining["password"] not in rendered
    assert joining["phone_number"] not in rendered
