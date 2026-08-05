import pytest
from starlette.websockets import WebSocketDisconnect

from climahealth.infrastructure.seed.users import (
    MADINA_PASSWORD,
    MADINA_USERNAME,
    NATIONAL_PASSWORD,
    NATIONAL_USERNAME,
)
from tests.api.conftest import token_for

MADINA_REPORT = {
    "district_id": "madina",
    "report_type": "flooding",
    "note": "Water rising fast at the junction",
}


def ticket_for(client, token: str) -> str:
    response = client.post("/ws/ticket", headers={"Authorization": f"Bearer {token}"})
    return response.json()["ticket"]


def test_a_connection_without_a_ticket_is_rejected(client):
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws") as socket:
        socket.receive_json()


def test_an_invalid_ticket_closes_the_socket(client):
    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect("/ws?ticket=not-a-real-ticket") as socket,
    ):
        socket.receive_json()


def test_a_national_subscriber_receives_a_report_event(client, national_headers):
    token = token_for(client, NATIONAL_USERNAME, NATIONAL_PASSWORD)

    with client.websocket_connect(f"/ws?ticket={ticket_for(client, token)}") as socket:
        client.post("/reports", json=MADINA_REPORT, headers=national_headers)
        event = socket.receive_json()

    assert event["event_type"] == "report_submitted"
    assert event["district_id"] == "madina"
    assert event["resource_id"]
    assert "flooding" in event["summary"]


def test_a_demo_override_is_broadcast(client, national_headers):
    token = token_for(client, NATIONAL_USERNAME, NATIONAL_PASSWORD)

    with client.websocket_connect(f"/ws?ticket={ticket_for(client, token)}") as socket:
        client.post(
            "/demo/set-conditions",
            json={"district_id": "madina", "scenario": "heavy_rain"},
            headers=national_headers,
        )
        event = socket.receive_json()

    assert event["event_type"] == "district_conditions_changed"
    assert event["district_id"] == "madina"


def test_an_incident_action_update_is_broadcast(client, national_headers):
    token = token_for(client, NATIONAL_USERNAME, NATIONAL_PASSWORD)

    with client.websocket_connect(f"/ws?ticket={ticket_for(client, token)}") as socket:
        client.post(
            "/incident/madina/action",
            json={"action_id": "madina-2", "status": "complete"},
            headers=national_headers,
        )
        event = socket.receive_json()

    assert event["event_type"] == "incident_action_updated"
    assert event["resource_id"] == "madina-2"
    assert "complete" in event["summary"]


def test_a_district_subscriber_never_receives_another_districts_event(client, national_headers):
    madina_token = token_for(client, MADINA_USERNAME, MADINA_PASSWORD)

    with client.websocket_connect(f"/ws?ticket={ticket_for(client, madina_token)}") as socket:
        client.post(
            "/demo/set-conditions",
            json={"district_id": "wa", "scenario": "dry_and_dusty"},
            headers=national_headers,
        )
        client.post(
            "/demo/set-conditions",
            json={"district_id": "madina", "scenario": "heavy_rain"},
            headers=national_headers,
        )
        event = socket.receive_json()

    assert event["district_id"] == "madina"


def test_the_subscriber_is_released_when_the_socket_closes(client):
    token = token_for(client, NATIONAL_USERNAME, NATIONAL_PASSWORD)
    broadcaster = client.app.state.broadcaster

    with client.websocket_connect(f"/ws?ticket={ticket_for(client, token)}"):
        assert broadcaster.subscriber_count == 1

    assert broadcaster.subscriber_count == 0


def test_a_ticket_cannot_be_used_twice(client):
    """A stream URL ends up in logs and proxy history, so it must not stay valid."""
    token = token_for(client, NATIONAL_USERNAME, NATIONAL_PASSWORD)
    ticket = ticket_for(client, token)

    with client.websocket_connect(f"/ws?ticket={ticket}"):
        pass

    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect(f"/ws?ticket={ticket}") as socket,
    ):
        socket.receive_json()


def test_the_bearer_token_alone_will_not_open_the_stream(client):
    token = token_for(client, NATIONAL_USERNAME, NATIONAL_PASSWORD)

    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect(f"/ws?ticket={token}") as socket,
    ):
        socket.receive_json()
