import httpx
import pytest

from climahealth.infrastructure.storage.cloudinary_photos import CloudinaryPhotoStore
from climahealth.infrastructure.storage.photos import MAXIMUM_BYTES, PhotoRejected

JPEG = b"\xff\xd8\xff\xe0" + b"padding"


def store_with(handler) -> CloudinaryPhotoStore:
    return CloudinaryPhotoStore(
        cloud_name="test-cloud",
        api_key="key",
        api_secret="secret",
        folder="climahealth/reports",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_the_url_cloudinary_returns_is_what_gets_stored():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"secure_url": "https://res.cloudinary.com/x/a.jpg"})

    assert store_with(handler).save(JPEG, "image/jpeg") == "https://res.cloudinary.com/x/a.jpg"


def test_the_same_photo_twice_uses_the_same_public_id():
    """Content addressing means a resend costs one stored file, and a reference
    cannot be guessed from a report id."""
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.content.decode("latin-1")
        seen.append(body.split('name="public_id"')[1].split("\r\n\r\n")[1].split("\r\n")[0])
        return httpx.Response(200, json={"secure_url": "https://res.cloudinary.com/x/a.jpg"})

    photos = store_with(handler)
    photos.save(JPEG, "image/jpeg")
    photos.save(JPEG, "image/jpeg")

    assert seen[0] == seen[1]


def test_a_failed_upload_says_so_rather_than_returning_a_broken_reference():
    """A report whose photo silently vanished is worse than one that says to retry."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    with pytest.raises(PhotoRejected):
        store_with(handler).save(JPEG, "image/jpeg")


def test_a_response_without_a_url_is_refused():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": {"message": "no"}})

    with pytest.raises(PhotoRejected):
        store_with(handler).save(JPEG, "image/jpeg")


@pytest.mark.parametrize(
    ("content", "content_type"),
    [(JPEG, "application/pdf"), (b"", "image/jpeg"), (b"x" * (MAXIMUM_BYTES + 1), "image/jpeg")],
)
def test_what_cannot_be_a_report_photo_never_reaches_the_network(content, content_type):
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("should not have been uploaded")

    with pytest.raises(PhotoRejected):
        store_with(handler).save(content, content_type)


def test_nothing_is_served_locally_because_the_reference_is_already_a_url():
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("not called")

    assert store_with(handler).find("https://res.cloudinary.com/x/a.jpg") is None
