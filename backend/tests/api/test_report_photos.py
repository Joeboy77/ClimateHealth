import struct
import zlib

from fastapi.testclient import TestClient


def png_bytes() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
        + chunk(b"IEND", b"")
    )


def upload(client: TestClient, headers: dict[str, str], content: bytes, kind: str):
    return client.post(
        "/reports/photo",
        headers={**headers, "Content-Type": kind},
        content=content,
    )


def test_a_photo_is_stored_and_can_be_read_back(client: TestClient, madina_headers: dict[str, str]):
    response = upload(client, madina_headers, png_bytes(), "image/png")

    assert response.status_code == 201
    reference = response.json()["photo_reference"]

    fetched = client.get(f"/reports/photo/{reference}", headers=madina_headers)
    assert fetched.status_code == 200
    assert fetched.content == png_bytes()


def test_the_same_photo_twice_is_stored_once(client: TestClient, madina_headers: dict[str, str]):
    """Content addressing: a resend after a dropped connection costs nothing extra."""
    first = upload(client, madina_headers, png_bytes(), "image/png").json()
    second = upload(client, madina_headers, png_bytes(), "image/png").json()

    assert first["photo_reference"] == second["photo_reference"]


def test_something_that_is_not_an_image_is_refused(
    client: TestClient, madina_headers: dict[str, str]
):
    response = upload(client, madina_headers, b"#!/bin/sh\nrm -rf /", "text/plain")

    assert response.status_code == 422


def test_an_empty_body_is_refused(client: TestClient, madina_headers: dict[str, str]):
    response = upload(client, madina_headers, b"", "image/png")

    assert response.status_code == 422


def test_a_photo_needs_a_signed_in_caller(client: TestClient):
    """A photograph of somebody's yard is not public the way a risk level is."""
    assert upload(client, {}, png_bytes(), "image/png").status_code == 401
    assert client.get("/reports/photo/anything.png").status_code == 401


def test_a_reference_cannot_climb_out_of_the_photo_directory(
    client: TestClient, madina_headers: dict[str, str]
):
    response = client.get("/reports/photo/..%2f..%2fpyproject.toml", headers=madina_headers)

    assert response.status_code == 404


def test_a_report_carries_its_photo_reference(client: TestClient, madina_headers: dict[str, str]):
    reference = upload(client, madina_headers, png_bytes(), "image/png").json()["photo_reference"]

    report = client.post(
        "/reports",
        headers=madina_headers,
        json={
            "district_id": "madina",
            "report_type": "stagnant_water",
            "note": "Standing water behind the market",
            "photo_reference": reference,
        },
    )

    assert report.status_code == 201
    assert report.json()["photo_reference"] == reference
