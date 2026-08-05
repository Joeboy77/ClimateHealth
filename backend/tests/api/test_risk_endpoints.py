import pytest

PROTECTED_ROUTES = (
    "/districts",
    "/districts/madina",
    "/risk/madina",
    "/forecast/madina",
)


@pytest.mark.parametrize("route", PROTECTED_ROUTES)
def test_every_data_route_requires_authentication(client, route):
    assert client.get(route).status_code == 401


def test_national_user_sees_every_district(client, national_headers):
    response = client.get("/districts", headers=national_headers)

    assert response.status_code == 200
    assert len(response.json()) >= 5
    assert {"madina", "wa"} <= {item["district_id"] for item in response.json()}


def test_district_user_sees_only_their_own_district(client, madina_headers):
    response = client.get("/districts", headers=madina_headers)

    assert [item["district_id"] for item in response.json()] == ["madina"]


def test_district_summary_carries_map_fields_and_risk_level(client, national_headers):
    summary = client.get("/districts", headers=national_headers).json()[0]

    assert set(summary) == {
        "district_id",
        "name",
        "region",
        "latitude",
        "longitude",
        "in_meningitis_belt",
        "overall_risk_level",
        "leading_condition",
        "generated_on",
        "season",
        "climate",
    }


def test_district_summary_carries_climate_for_the_map_layers(client, national_headers):
    summary = client.get("/districts", headers=national_headers).json()[0]

    assert summary["climate"]["rainfall_7d_mm"] >= 0
    assert 0 <= summary["climate"]["humidity_mean_percent"] <= 100
    assert summary["climate"]["temperature_max_c"] is not None
    assert summary["climate"]["provenance"] in {"live", "demo"}


def test_district_detail_includes_climate_and_ranked_risks(client, national_headers):
    body = client.get("/districts/wa", headers=national_headers).json()

    assert body["district_id"] == "wa"
    assert body["climate"]["observed_on"] == "2026-07-27"
    assert body["risks"]
    scores = [risk["score"] for risk in body["risks"]]
    assert scores == sorted(scores, reverse=True)


def test_district_user_is_forbidden_from_another_district_detail(client, madina_headers):
    assert client.get("/districts/wa", headers=madina_headers).status_code == 403


def test_district_user_is_forbidden_from_another_districts_risk(client, madina_headers):
    assert client.get("/risk/wa", headers=madina_headers).status_code == 403


def test_district_user_is_forbidden_from_another_districts_forecast(client, madina_headers):
    assert client.get("/forecast/wa", headers=madina_headers).status_code == 403


def test_district_user_may_read_their_own_district(client, madina_headers):
    assert client.get("/risk/madina", headers=madina_headers).status_code == 200


def test_unknown_district_is_not_found(client, national_headers):
    assert client.get("/risk/atlantis", headers=national_headers).status_code == 404


def test_risk_response_carries_the_full_contract(client, national_headers):
    body = client.get("/risk/madina", headers=national_headers).json()

    assert body["district_id"] == "madina"
    assert body["overall_risk_level"] in {"low", "moderate", "high", "severe"}
    risk = body["risks"][0]
    assert set(risk) == {
        "condition",
        "level",
        "score",
        "lag_window",
        "vulnerable_group",
        "reasons",
        "confidence",
    }
    assert set(risk["lag_window"]) == {"minimum_days", "maximum_days"}


def test_forecast_returns_friendly_text_and_a_single_action(client, national_headers):
    body = client.get("/forecast/madina", headers=national_headers).json()

    assert body["headline"]
    assert body["summary"]
    assert body["action_today"]
    assert body["language"] == "en"
    assert len(body["top_risks"]) <= 3


def test_forecast_can_be_phrased_for_an_officer(client, national_headers):
    citizen = client.get("/forecast/madina", headers=national_headers).json()
    officer = client.get(
        "/forecast/madina", headers=national_headers, params={"audience": "officer"}
    ).json()

    assert officer["action_today"] != citizen["action_today"]
    assert officer["top_risks"] == citizen["top_risks"]


def test_meningitis_is_absent_from_a_southern_district_in_the_wet_season(client, national_headers):
    body = client.get("/risk/madina", headers=national_headers).json()

    assert "meningitis" not in {risk["condition"] for risk in body["risks"]}
