MADINA_REPORT = {
    "district_id": "madina",
    "report_type": "stagnant_water",
    "note": "Water pooling behind the lorry station for several days",
    "latitude": 5.684,
    "longitude": -0.167,
}


def test_submitting_a_report_returns_it_with_an_identifier(client, madina_headers):
    response = client.post("/reports", json=MADINA_REPORT, headers=madina_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["report_id"]
    assert body["district_id"] == "madina"
    assert body["report_type"] == "stagnant_water"
    assert body["submitted_on"] == "2026-07-27"


def test_a_submitted_report_is_attributed_to_the_caller(client, madina_headers):
    body = client.post("/reports", json=MADINA_REPORT, headers=madina_headers).json()

    assert body["submitted_by"] == "user-madina"


def test_a_district_user_cannot_report_for_another_district(client, madina_headers):
    response = client.post(
        "/reports", json={**MADINA_REPORT, "district_id": "wa"}, headers=madina_headers
    )

    assert response.status_code == 403


def test_reporting_for_an_unknown_district_is_not_found(client, national_headers):
    response = client.post(
        "/reports", json={**MADINA_REPORT, "district_id": "atlantis"}, headers=national_headers
    )

    assert response.status_code == 404


def test_an_empty_note_is_rejected(client, madina_headers):
    response = client.post("/reports", json={**MADINA_REPORT, "note": ""}, headers=madina_headers)

    assert response.status_code == 422


def test_an_unknown_report_type_is_rejected(client, madina_headers):
    response = client.post(
        "/reports", json={**MADINA_REPORT, "report_type": "alien_sighting"}, headers=madina_headers
    )

    assert response.status_code == 422


def test_a_national_user_sees_reports_from_every_district(client, national_headers):
    districts = {
        report["district_id"] for report in client.get("/reports", headers=national_headers).json()
    }

    assert {"madina", "wa"} <= districts


def test_a_district_user_sees_only_their_own_districts_reports(client, madina_headers):
    districts = {
        report["district_id"] for report in client.get("/reports", headers=madina_headers).json()
    }

    assert districts == {"madina"}


def test_reports_can_be_filtered_by_district(client, national_headers):
    reports = client.get("/reports", headers=national_headers, params={"district_id": "wa"}).json()

    assert {report["district_id"] for report in reports} == {"wa"}


def test_reports_can_be_filtered_by_type(client, national_headers):
    reports = client.get(
        "/reports", headers=national_headers, params={"report_type": "dust_haze"}
    ).json()

    assert {report["report_type"] for report in reports} == {"dust_haze"}


def test_filtering_by_a_forbidden_district_is_refused(client, madina_headers):
    response = client.get("/reports", headers=madina_headers, params={"district_id": "wa"})

    assert response.status_code == 403


def test_a_newly_submitted_report_appears_in_the_list(client, madina_headers):
    created = client.post("/reports", json=MADINA_REPORT, headers=madina_headers).json()

    listed = client.get("/reports", headers=madina_headers).json()

    assert created["report_id"] in {report["report_id"] for report in listed}


def test_a_single_report_can_be_fetched_by_id(client, national_headers):
    response = client.get("/reports/report-seed-1", headers=national_headers)

    assert response.status_code == 200
    assert response.json()["report_id"] == "report-seed-1"


def test_an_unknown_report_is_not_found(client, national_headers):
    assert client.get("/reports/nope", headers=national_headers).status_code == 404


def test_a_district_user_cannot_read_another_districts_report(client, madina_headers):
    response = client.get("/reports/report-seed-3", headers=madina_headers)

    assert response.status_code == 403


def test_submitting_a_report_requires_authentication(client):
    assert client.post("/reports", json=MADINA_REPORT).status_code == 401
