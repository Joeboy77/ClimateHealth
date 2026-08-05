from climahealth.infrastructure.seed.users import (
    MADINA_PASSWORD,
    MADINA_USERNAME,
    NATIONAL_PASSWORD,
    NATIONAL_USERNAME,
)


def test_health_endpoint_is_open(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_login_returns_a_token_and_national_scope(client):
    response = client.post(
        "/login", json={"username": NATIONAL_USERNAME, "password": NATIONAL_PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["scope"] == {"level": "national", "district_id": None}


def test_login_returns_the_district_scope_for_a_district_officer(client):
    response = client.post(
        "/login", json={"username": MADINA_USERNAME, "password": MADINA_PASSWORD}
    )

    assert response.json()["user"]["scope"] == {"level": "district", "district_id": "madina"}


def test_login_with_a_bad_password_is_unauthorised(client):
    response = client.post(
        "/login", json={"username": NATIONAL_USERNAME, "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_login_with_an_unknown_user_is_unauthorised(client):
    response = client.post("/login", json={"username": "ghost", "password": "whatever"})

    assert response.status_code == 401


def test_login_with_a_missing_field_is_a_validation_error(client):
    assert client.post("/login", json={"username": NATIONAL_USERNAME}).status_code == 422


def test_me_returns_the_callers_scope(client, madina_headers):
    response = client.get("/me", headers=madina_headers)

    assert response.status_code == 200
    assert response.json()["scope"]["district_id"] == "madina"
    assert response.json()["username"] == MADINA_USERNAME


def test_me_without_a_token_is_unauthorised(client):
    assert client.get("/me").status_code == 401


def test_me_with_a_malformed_token_is_unauthorised(client):
    response = client.get("/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_password_is_never_echoed_back(client):
    response = client.post(
        "/login", json={"username": NATIONAL_USERNAME, "password": NATIONAL_PASSWORD}
    )

    assert NATIONAL_PASSWORD not in response.text
