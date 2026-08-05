HEAVY_RAIN = {"district_id": "madina", "scenario": "heavy_rain"}
DRY_AND_DUSTY = {"district_id": "wa", "scenario": "dry_and_dusty"}


def test_demo_override_requires_authentication(client):
    assert client.post("/demo/set-conditions", json=HEAVY_RAIN).status_code == 401


def test_heavy_rain_scenario_drives_madina_malaria_up(client, national_headers):
    before = client.get("/risk/madina", headers=national_headers).json()

    applied = client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)
    after = client.get("/risk/madina", headers=national_headers).json()

    assert applied.status_code == 200
    assert applied.json()["climate"]["rainfall_7d_mm"] == 120.0
    malaria_before = next(r for r in before["risks"] if r["condition"] == "malaria")["score"]
    malaria_after = next(r for r in after["risks"] if r["condition"] == "malaria")["score"]
    assert malaria_after > malaria_before
    assert after["risks"][0]["level"] in {"high", "severe"}


def test_heavy_rain_puts_a_water_borne_disease_at_the_top(client, national_headers):
    """Flooding drives cholera and diarrhoea faster than it drives malaria."""
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    body = client.get("/risk/madina", headers=national_headers).json()

    water_borne = {"cholera", "diarrhoeal_disease", "leptospirosis", "typhoid_fever"}
    raised = [r for r in body["risks"] if r["level"] in {"high", "severe"}]

    fast_water_borne = [
        r for r in raised if r["condition"] in water_borne and r["lag_window"]["maximum_days"] <= 21
    ]
    assert fast_water_borne, "flooding must raise at least one fast water-borne risk"


def test_heavy_rain_raises_several_conditions_not_only_one(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    body = client.get("/risk/madina", headers=national_headers).json()
    elevated = [r for r in body["risks"] if r["level"] in {"high", "severe"}]

    assert len({r["condition"] for r in elevated}) >= 3


def test_dry_and_dusty_scenario_drives_wa_meningitis_up(client, national_headers):
    client.post("/demo/set-conditions", json=DRY_AND_DUSTY, headers=national_headers)

    body = client.get("/risk/wa", headers=national_headers).json()

    meningitis = next(r for r in body["risks"] if r["condition"] == "meningitis")
    assert meningitis["level"] in {"high", "severe"}
    assert meningitis["reasons"]


def test_overridden_climate_is_reported_as_demo_confidence(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    body = client.get("/risk/madina", headers=national_headers).json()

    assert body["climate"]["provenance"] == "demo"
    assert all(risk["confidence"] in {"threshold", "baseline", "model"} for risk in body["risks"])


def test_an_override_affects_only_the_targeted_district(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    wa = client.get("/risk/wa", headers=national_headers).json()

    assert wa["climate"]["provenance"] == "live"


def test_explicit_values_override_the_scenario_defaults(client, national_headers):
    response = client.post(
        "/demo/set-conditions",
        json={"district_id": "madina", "scenario": "heavy_rain", "rainfall_7d_mm": 300.0},
        headers=national_headers,
    )

    assert response.json()["climate"]["rainfall_7d_mm"] == 300.0
    assert response.json()["climate"]["humidity_mean_percent"] == 85.0


def test_clearing_an_override_restores_live_data(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    cleared = client.delete("/demo/set-conditions/madina", headers=national_headers)
    body = client.get("/risk/madina", headers=national_headers).json()

    assert cleared.status_code == 204
    assert body["climate"]["provenance"] == "live"


def test_district_user_cannot_override_another_district(client, madina_headers):
    response = client.post("/demo/set-conditions", json=DRY_AND_DUSTY, headers=madina_headers)

    assert response.status_code == 403


def test_override_for_an_unknown_district_is_not_found(client, national_headers):
    response = client.post(
        "/demo/set-conditions",
        json={"district_id": "atlantis", "scenario": "heavy_rain"},
        headers=national_headers,
    )

    assert response.status_code == 404


def test_the_forecast_follows_the_demo_scenario(client, national_headers):
    client.post("/demo/set-conditions", json=HEAVY_RAIN, headers=national_headers)

    body = client.get("/forecast/madina", headers=national_headers).json()

    assert body["confidence"] in {"threshold", "baseline", "model"}
    assert body["headline"]
    assert body["action_today"]
    assert body["top_risks"][0]["level"] in {"high", "severe"}
