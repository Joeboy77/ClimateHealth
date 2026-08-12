from itertools import count

from fastapi.testclient import TestClient

from climahealth.services.rewards import POINTS_PER_NHIS_YEAR

_NUMBERS = count(1)


def join(client: TestClient, name: str = "Ama Serwaa", age_band: str = "18_34") -> dict:
    return client.post(
        "/citizens",
        json={
            "display_name": name,
            "district_id": "madina",
            "age_band": age_band,
            "language": "en",
            "phone_number": f"024{next(_NUMBERS):07d}",
            "password": "keep-well",
        },
    ).json()


def test_a_new_guardian_is_told_how_far_a_year_of_cover_is(client: TestClient):
    joined = join(client)
    headers = {"authorization": f"Bearer {joined['access_token']}"}

    quote = client.get(f"/rewards/quote/{joined['citizen']['user_id']}", headers=headers).json()

    assert quote["points_required"] == POINTS_PER_NHIS_YEAR
    assert quote["points_remaining"] == POINTS_PER_NHIS_YEAR
    assert quote["can_redeem"] is False
    assert "3500 more points" in quote["reason"]


def test_a_minor_is_told_they_are_already_exempt_rather_than_shown_a_target(
    client: TestClient,
):
    """Under-18s do not pay NHIS premiums, so there is nothing here for them to buy."""
    joined = join(client, age_band="13_17")
    headers = {"authorization": f"Bearer {joined['access_token']}"}

    quote = client.get(f"/rewards/quote/{joined['citizen']['user_id']}", headers=headers).json()

    assert quote["can_redeem"] is False
    assert "exempt" in quote["reason"]


def test_claiming_without_enough_points_is_refused(client: TestClient):
    joined = join(client)
    headers = {"authorization": f"Bearer {joined['access_token']}"}

    refused = client.post(
        "/rewards/redeem",
        json={"user_id": joined["citizen"]["user_id"]},
        headers=headers,
    )

    assert refused.status_code == 409


def test_the_renewal_queue_is_ghana_health_service_only(client: TestClient, epa_headers):
    """It carries names and phone numbers, which not every agency needs to see."""
    assert client.get("/guardian/leaderboard/standings", headers=epa_headers).status_code == 403


def test_the_queue_ranks_guardians_and_says_how_far_each_has_to_go(
    client: TestClient, national_headers
):
    join(client, name="Ama Serwaa")
    join(client, name="Kofi Mensah")

    queue = client.get(
        "/guardian/leaderboard/standings?district_id=madina", headers=national_headers
    ).json()

    assert len(queue) == 2
    assert [row["points"] for row in queue] == sorted(
        [row["points"] for row in queue], reverse=True
    )
    for row in queue:
        assert row["phone_number"] is not None
        assert row["points_remaining"] == POINTS_PER_NHIS_YEAR - row["points"]


def test_seeded_staff_guardians_are_not_offered_nhis_cover(client: TestClient, national_headers):
    """Demonstration and staff guardians have no citizen record. A renewal queue
    listing them would be offering cover to rows that are not people."""
    queue = client.get("/guardian/leaderboard/standings", headers=national_headers).json()

    assert queue == []
