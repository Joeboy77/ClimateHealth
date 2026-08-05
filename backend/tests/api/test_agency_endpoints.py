import pytest

HEAVY_RAIN = {"district_id": "madina", "scenario": "heavy_rain"}
DRY_AND_DUSTY = {"district_id": "wa", "scenario": "dry_and_dusty"}

PROTECTED_ROUTES = (
    "/alerts",
    "/incident/madina",
    "/readiness/madina",
    "/reports",
)


@pytest.mark.parametrize("route", PROTECTED_ROUTES)
def test_agency_routes_require_authentication(client, route):
    assert client.get(route).status_code == 401


def test_alerts_are_raised_from_real_engine_output(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    alerts = client.get("/alerts", headers=national_headers).json()

    malaria = next(
        alert
        for alert in alerts
        if alert["district_id"] == "madina" and alert["condition"] == "malaria"
    )
    assert malaria["level"] in {"high", "severe"}
    assert malaria["reasons"]
    assert malaria["recommended_action"]
    assert malaria["lag_window"] == {"minimum_days": 14, "maximum_days": 42}


def test_alerts_carry_officer_wording_not_citizen_wording(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    alerts = client.get("/alerts", headers=national_headers).json()
    malaria = next(alert for alert in alerts if alert["condition"] == "malaria")

    assert "rapid diagnostic" in malaria["recommended_action"].lower()


def test_alerts_are_ranked_by_score(client, national_headers):
    scores = [alert["score"] for alert in client.get("/alerts", headers=national_headers).json()]

    assert scores == sorted(scores, reverse=True)


def test_only_high_and_severe_risks_become_alerts(client, national_headers):
    alerts = client.get("/alerts", headers=national_headers).json()

    assert all(alert["level"] in {"high", "severe"} for alert in alerts)


def test_a_district_user_sees_only_their_own_alerts(client, madina_headers, national_headers):
    client.post("/demo/set-conditions", json=DRY_AND_DUSTY, headers=national_headers)

    alerts = client.get("/alerts", headers=madina_headers).json()

    assert {alert["district_id"] for alert in alerts} <= {"madina"}


def test_a_single_alert_can_be_fetched_by_id(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)
    alert_id = client.get("/alerts", headers=national_headers).json()[0]["alert_id"]

    response = client.get(f"/alerts/{alert_id}", headers=national_headers)

    assert response.status_code == 200
    assert response.json()["alert_id"] == alert_id


def test_an_unknown_alert_is_not_found(client, national_headers):
    assert client.get("/alerts/nope", headers=national_headers).status_code == 404


def test_a_district_user_cannot_fetch_another_districts_alert(
    client, national_headers, madina_headers
):
    client.post("/demo/set-conditions", json=DRY_AND_DUSTY, headers=national_headers)
    wa_alerts = [
        alert
        for alert in client.get("/alerts", headers=national_headers).json()
        if alert["district_id"] == "wa"
    ]

    response = client.get(f"/alerts/{wa_alerts[0]['alert_id']}", headers=madina_headers)

    assert response.status_code == 404


def test_the_incident_room_lists_assigned_agency_actions(client, national_headers):
    body = client.get("/incident/madina", headers=national_headers).json()

    assert body["district_id"] == "madina"
    assert len(body["actions"]) >= 3
    assert {action["agency"] for action in body["actions"]}


def test_an_action_status_can_be_updated(client, national_headers):
    response = client.post(
        "/incident/madina/action",
        json={"action_id": "madina-2", "status": "complete"},
        headers=national_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "complete"


def test_an_updated_status_persists_in_the_incident_room(client, national_headers):
    client.post(
        "/incident/madina/action",
        json={"action_id": "madina-2", "status": "in_progress"},
        headers=national_headers,
    )

    body = client.get("/incident/madina", headers=national_headers).json()

    action = next(item for item in body["actions"] if item["action_id"] == "madina-2")
    assert action["status"] == "in_progress"


def test_an_action_from_another_district_cannot_be_updated(client, national_headers):
    response = client.post(
        "/incident/madina/action",
        json={"action_id": "wa-1", "status": "complete"},
        headers=national_headers,
    )

    assert response.status_code == 404


def test_a_district_user_cannot_touch_another_districts_incident_room(client, madina_headers):
    assert client.get("/incident/wa", headers=madina_headers).status_code == 403


def test_a_shortfall_carries_the_hours_left_before_cases_arrive(client, national_headers):
    """A shortfall matters against the date the ward fills up, not in the abstract."""
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    body = client.get("/readiness/madina", headers=national_headers).json()
    short = [item for item in body["resources"] if item["shortfall_units"] > 0]

    assert short
    assert all(item["hours_to_dispatch"] is not None for item in short)
    assert body["hours_to_dispatch"] == min(item["hours_to_dispatch"] for item in short)


def test_a_stocked_resource_has_no_dispatch_deadline(client, national_headers):
    body = client.get("/readiness/madina", headers=national_headers).json()
    stocked = [item for item in body["resources"] if item["shortfall_units"] == 0]

    assert all(item["hours_to_dispatch"] is None for item in stocked)


def test_readiness_compares_risk_against_stock(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    body = client.get("/readiness/madina", headers=national_headers).json()

    assert body["overall_risk_level"] in {"high", "severe"}
    assert body["resources"]
    assert body["status"] in {"ready", "stretched", "critical", "emergency"}


def test_rising_risk_raises_the_required_units(client, national_headers):
    calm = client.get("/readiness/madina", headers=national_headers).json()
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)
    severe = client.get("/readiness/madina", headers=national_headers).json()

    calm_required = {r["resource"]: r["required_units"] for r in calm["resources"]}
    severe_required = {r["resource"]: r["required_units"] for r in severe["resources"]}

    assert all(severe_required[name] > calm_required[name] for name in calm_required)


def test_readiness_counts_open_community_reports(client, national_headers):
    body = client.get("/readiness/madina", headers=national_headers).json()

    assert body["open_reports"] >= 2


def test_a_district_user_is_refused_another_districts_readiness(client, madina_headers):
    assert client.get("/readiness/wa", headers=madina_headers).status_code == 403


def test_a_coordinator_may_move_any_agency_action(client, madina_headers):
    """The district health officer coordinates: they can move Assembly work."""
    response = client.post(
        "/incident/madina/action",
        json={"action_id": "madina-2", "status": "complete"},
        headers=madina_headers,
    )

    assert response.status_code == 200
    assert response.json()["agency"] == "assembly"


def test_a_responder_cannot_move_another_agencys_action(client, nadmo_headers):
    """NADMO may not close a Ghana Health Service action."""
    response = client.post(
        "/incident/madina/action",
        json={"action_id": "madina-1", "status": "complete"},
        headers=nadmo_headers,
    )

    assert response.status_code == 403
    assert "Ghana Health Service" in response.json()["detail"]


def test_a_responder_may_move_their_own_agencys_action(client, madina_headers, nadmo_headers):
    created = client.post(
        "/incident/madina/assign",
        json={
            "agency": "nadmo",
            "description": "Sandbag the low-lying market approach",
            "due_on": "2026-08-20",
        },
        headers=madina_headers,
    ).json()

    response = client.post(
        "/incident/madina/action",
        json={"action_id": created["action_id"], "status": "in_progress"},
        headers=nadmo_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_only_a_coordinator_may_assign_work(client, nadmo_headers):
    response = client.post(
        "/incident/madina/assign",
        json={
            "agency": "nadmo",
            "description": "Self-assigned task",
            "due_on": "2026-08-20",
        },
        headers=nadmo_headers,
    )

    assert response.status_code == 403
    assert "coordinator" in response.json()["detail"].lower()


def test_an_assignment_records_who_made_it(client, madina_headers):
    created = client.post(
        "/incident/madina/assign",
        json={
            "agency": "epa",
            "description": "Sample air quality near the refuse site",
            "due_on": "2026-08-18",
            "location_name": "Madina transfer station",
            "latitude": 5.69,
            "longitude": -0.168,
        },
        headers=madina_headers,
    ).json()

    assert created["assigned_by"] == "Kwame Boateng"
    assert "District Health Officer" in created["assigned_by_role"]
    assert created["status"] == "not_started"
    assert created["updated_by"] is None


def test_a_status_change_records_who_moved_it(client, madina_headers):
    client.post(
        "/incident/madina/action",
        json={"action_id": "madina-3", "status": "in_progress"},
        headers=madina_headers,
    )

    room = client.get("/incident/madina", headers=madina_headers).json()
    action = next(a for a in room["actions"] if a["action_id"] == "madina-3")

    assert action["updated_by"] == "Kwame Boateng"
    assert action["updated_by_agency"] == "ghs"
    assert action["updated_at"] is not None


def test_the_seeded_actions_record_who_assigned_them(client, madina_headers):
    room = client.get("/incident/madina", headers=madina_headers).json()

    assert all(action["assigned_by"] for action in room["actions"])
    assert all(action["assigned_on"] for action in room["actions"])


def test_me_reports_the_users_role_and_assignment_rights(client, madina_headers, nadmo_headers):
    coordinator = client.get("/me", headers=madina_headers).json()
    responder = client.get("/me", headers=nadmo_headers).json()

    assert coordinator["role"] == "coordinator"
    assert coordinator["can_assign_actions"] is True
    assert responder["role"] == "responder"
    assert responder["can_assign_actions"] is False


def test_the_playbook_creates_agency_tasks_without_a_coordinator(client, national_headers):
    """A raised condition is itself the instruction. Nobody assigns these."""
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    room = client.get("/incident/madina", headers=national_headers).json()
    playbook = [a for a in room["actions"] if a["origin"] == "playbook"]

    assert len(playbook) >= 4
    assert all(a["assigned_by"] == "ClimaHealth playbook" for a in playbook)
    assert all(a["source_condition"] for a in playbook)


def test_the_playbook_reaches_several_agencies_not_only_health(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    room = client.get("/incident/madina", headers=national_headers).json()
    agencies = {a["agency"] for a in room["actions"] if a["origin"] == "playbook"}

    assert "ghs" in agencies
    assert len(agencies) >= 2


def test_each_playbook_task_names_the_condition_that_caused_it(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    room = client.get("/incident/madina", headers=national_headers).json()
    risks = client.get("/risk/madina", headers=national_headers).json()
    raised = {r["condition"] for r in risks["risks"] if r["level"] in {"high", "severe"}}

    for action in room["actions"]:
        if action["origin"] == "playbook":
            assert action["source_condition"] in raised


def test_a_playbook_task_keeps_its_status_across_recomputation(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)
    room = client.get("/incident/madina", headers=national_headers).json()
    task = next(a for a in room["actions"] if a["origin"] == "playbook")

    client.post(
        "/incident/madina/action",
        json={"action_id": task["action_id"], "status": "in_progress"},
        headers=national_headers,
    )
    again = client.get("/incident/madina", headers=national_headers).json()

    same = next(a for a in again["actions"] if a["action_id"] == task["action_id"])
    assert same["status"] == "in_progress"


def test_every_status_change_is_recorded_in_an_append_only_history(client, national_headers):
    client.post(
        "/incident/madina/action",
        json={"action_id": "madina-3", "status": "in_progress"},
        headers=national_headers,
    )
    client.post(
        "/incident/madina/action",
        json={"action_id": "madina-3", "status": "blocked"},
        headers=national_headers,
    )
    client.post(
        "/incident/madina/action",
        json={"action_id": "madina-3", "status": "complete"},
        headers=national_headers,
    )

    room = client.get("/incident/madina", headers=national_headers).json()
    trail = [h for h in room["history"] if h["action_id"] == "madina-3"]

    assert [h["to_status"] for h in trail] == ["in_progress", "blocked", "complete"]
    assert [h["from_status"] for h in trail] == ["not_started", "in_progress", "blocked"]
    assert all(h["actor_name"] == "Akosua Mensah" for h in trail)
    assert all(h["occurred_at"] for h in trail)


def test_history_records_which_agency_and_role_made_each_move(
    client, madina_headers, nadmo_headers
):
    created = client.post(
        "/incident/madina/assign",
        json={
            "agency": "nadmo",
            "description": "Stage sandbags at the market approach",
            "due_on": "2026-08-20",
        },
        headers=madina_headers,
    ).json()

    client.post(
        "/incident/madina/action",
        json={"action_id": created["action_id"], "status": "in_progress"},
        headers=nadmo_headers,
    )
    client.post(
        "/incident/madina/action",
        json={"action_id": created["action_id"], "status": "complete"},
        headers=madina_headers,
    )

    room = client.get("/incident/madina", headers=madina_headers).json()
    trail = [h for h in room["history"] if h["action_id"] == created["action_id"]]

    assert trail[0]["actor_agency"] == "nadmo"
    assert trail[0]["actor_role"] == "Agency responder"
    assert trail[1]["actor_agency"] == "ghs"
    assert trail[1]["actor_role"] == "Response coordinator"


def test_history_is_never_rewritten_by_a_later_move(client, national_headers):
    client.post(
        "/incident/madina/action",
        json={"action_id": "madina-1", "status": "complete"},
        headers=national_headers,
    )
    first = client.get("/incident/madina", headers=national_headers).json()["history"]

    client.post(
        "/incident/madina/action",
        json={"action_id": "madina-1", "status": "not_started"},
        headers=national_headers,
    )
    second = client.get("/incident/madina", headers=national_headers).json()["history"]

    assert second[: len(first)] == first
    assert len(second) == len(first) + 1
