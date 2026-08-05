import pytest

REQUIRED_ROUTES: tuple[tuple[str, str], ...] = (
    ("POST", "/login"),
    ("GET", "/me"),
    ("GET", "/districts"),
    ("GET", "/districts/{district_id}"),
    ("GET", "/risk/{district_id}"),
    ("GET", "/forecast/{district_id}"),
    ("POST", "/demo/set-conditions"),
    ("GET", "/alerts"),
    ("GET", "/alerts/{alert_id}"),
    ("GET", "/incident/{district_id}"),
    ("POST", "/incident/{district_id}/action"),
    ("GET", "/readiness/{district_id}"),
    ("POST", "/reports"),
    ("GET", "/reports"),
    ("GET", "/reports/{report_id}"),
    ("GET", "/guardian/{user_id}"),
    ("GET", "/quiz/daily/{district_id}"),
    ("POST", "/quiz/answer"),
    ("POST", "/guardian/mission"),
    ("GET", "/rewards/{user_id}"),
    ("GET", "/shield/{district_id}"),
)

DISTRICT_SCOPED_ROUTES: tuple[str, ...] = (
    "/districts/wa",
    "/risk/wa",
    "/forecast/wa",
    "/incident/wa",
    "/readiness/wa",
    "/quiz/daily/wa",
    "/shield/wa",
)


@pytest.mark.parametrize(("method", "path"), REQUIRED_ROUTES)
def test_every_agreed_endpoint_is_published(client, method, path):
    schema = client.get("/openapi.json").json()

    assert path in schema["paths"], f"{path} is missing from the API"
    assert method.lower() in schema["paths"][path]


def registered_paths(routes) -> set[str]:
    paths: set[str] = set()
    for route in routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths.add(path)
        nested = getattr(route, "original_router", None) or getattr(route, "routes", None)
        if nested is not None:
            paths |= registered_paths(getattr(nested, "routes", nested))
    return paths


def test_the_websocket_route_is_registered(client):
    assert "/ws" in registered_paths(client.app.routes)


@pytest.mark.parametrize("path", DISTRICT_SCOPED_ROUTES)
def test_every_district_scoped_route_refuses_a_foreign_district(client, madina_headers, path):
    assert client.get(path, headers=madina_headers).status_code == 403


@pytest.mark.parametrize("path", DISTRICT_SCOPED_ROUTES)
def test_every_district_scoped_route_requires_a_token(client, path):
    assert client.get(path).status_code == 401


def test_the_openapi_schema_documents_the_service(client):
    schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "ClimaHealth Predict"
    assert schema["info"]["version"]
    assert schema["info"]["description"]


def test_unknown_districts_are_consistently_not_found(client, national_headers):
    for path in ("/districts/atlantis", "/risk/atlantis", "/incident/atlantis"):
        assert client.get(path, headers=national_headers).status_code == 404
