from fastapi.testclient import TestClient


def test_a_district_user_cannot_preview_another_districts_message(
    client: TestClient, madina_headers: dict[str, str]
):
    response = client.get("/outreach/sms/wa", headers=madina_headers)

    assert response.status_code == 403


def test_the_preview_reports_the_delivery_mode_so_nobody_assumes_it_sent(
    client: TestClient, national_headers: dict[str, str]
):
    response = client.get("/outreach/sms/madina", headers=national_headers)

    assert response.status_code == 200
    assert response.json()["delivery_mode"] == "preview"


def test_a_responder_may_not_broadcast(client: TestClient, nadmo_headers: dict[str, str]):
    response = client.post(
        "/outreach/sms/madina",
        headers=nadmo_headers,
        json={"recipients": ["233241234567"]},
    )

    assert response.status_code == 403


def test_a_coordinator_broadcast_stays_a_preview_until_delivery_is_switched_on(
    client: TestClient, national_headers: dict[str, str]
):
    client.post(
        "/demo/set-conditions",
        headers=national_headers,
        json={"district_id": "madina", "scenario": "heavy_rain"},
    )

    response = client.post(
        "/outreach/sms/madina",
        headers=national_headers,
        json={"recipients": ["233241234567", "233551112222"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["sent"] is False
    assert body["preview_only"] is True
    assert len(body["deliveries"]) == 2
    assert {delivery["provider_code"] for delivery in body["deliveries"]} == {"PREVIEW"}


def test_broadcasting_a_district_with_nothing_raised_is_refused(
    client: TestClient, national_headers: dict[str, str]
):
    client.post(
        "/demo/set-conditions",
        headers=national_headers,
        json={"district_id": "madina", "scenario": "calm"},
    )

    response = client.post(
        "/outreach/sms/madina",
        headers=national_headers,
        json={"recipients": ["233241234567"]},
    )

    assert response.status_code == 409


def test_the_ussd_callback_needs_no_token_because_the_network_calls_it(client: TestClient):
    response = client.post(
        "/ussd/moolre",
        json={
            "sessionId": "3-1707465798",
            "new": True,
            "msisdn": "233241235993",
            "network": 3,
            "message": "",
            "extension": "109",
            "data": "",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] is True
    assert "Choose language" in body["message"]


def test_a_ussd_session_carries_its_choices_between_keypresses(client: TestClient):
    session = {
        "sessionId": "3-1707465799",
        "msisdn": "233241235993",
        "network": 3,
        "extension": "109",
        "data": "",
    }
    client.post("/ussd/moolre", json={**session, "new": True, "message": ""})

    regions = client.post("/ussd/moolre", json={**session, "new": False, "message": "1"})

    assert "Choose region" in regions.json()["message"]


def test_the_open_endpoint_is_rated_so_it_cannot_be_used_as_an_amplifier(
    client: TestClient,
):
    """It evaluates every district without a credential, so it needs a ceiling."""
    statuses = {client.get("/public/overview").status_code for _ in range(40)}

    assert 429 in statuses


AT_SESSION = {"sessionId": "ATUid_9f2c", "phoneNumber": "+233241235993", "serviceCode": "*920*55#"}


def test_africas_talking_opens_a_session_with_a_con_prefix(client: TestClient):
    """Africa's Talking reads the first word: CON keeps the session open, END closes it."""
    response = client.post("/ussd/africastalking", data={**AT_SESSION, "text": ""})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text.startswith("CON ")


def test_africas_talking_sends_the_whole_chain_not_the_latest_keypress(
    client: TestClient,
):
    """The caller has pressed 1 then 1. Africa's Talking posts "1*1", not "1"."""
    first = client.post("/ussd/africastalking", data={**AT_SESSION, "text": "1"})
    second = client.post("/ussd/africastalking", data={**AT_SESSION, "text": "1*1"})

    assert "Choose region" in first.text
    assert "Choose region" not in second.text


def test_a_replayed_chain_answers_the_same_way_without_a_stored_session(
    client: TestClient,
):
    """A restarted process or a retried request must still answer correctly, so the
    chain is replayed from the start rather than trusted to a stored session."""
    walked = client.post("/ussd/africastalking", data={**AT_SESSION, "text": "1"})
    client.post("/ussd/africastalking", data={**AT_SESSION, "text": "1*1"})

    replayed = client.post(
        "/ussd/africastalking", data={**AT_SESSION, "sessionId": "ATUid_other", "text": "1"}
    )

    assert replayed.text == walked.text


def test_the_network_is_read_from_the_number_because_africas_talking_omits_it(
    client: TestClient,
):
    response = client.post(
        "/ussd/africastalking", data={**AT_SESSION, "phoneNumber": "0201234567", "text": ""}
    )

    assert response.status_code == 200
    assert response.text.startswith("CON ")


def test_africas_talking_needs_no_token_because_the_network_calls_it(client: TestClient):
    assert client.post("/ussd/africastalking", data={**AT_SESSION, "text": ""}).status_code == 200
