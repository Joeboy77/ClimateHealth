import hashlib
import time
from pathlib import Path

import httpx

from climahealth.infrastructure.storage.photos import (
    ACCEPTED_TYPES,
    MAXIMUM_BYTES,
    PhotoRejected,
)

UPLOAD_TIMEOUT_SECONDS = 30.0


class CloudinaryPhotoStore:
    """Report photographs in Cloudinary, addressed by the URL it hands back.

    A report photograph is evidence: an officer standing in a flooded street needs to
    see what the person who filed it saw. Keeping them on the application server means
    they die with the container and cannot be served to a dashboard on another host, so
    they go to object storage and the report keeps the URL.

    The same content-addressed id as the local store, so the same photograph submitted
    twice costs one upload, and a reference still cannot be guessed from a report id.
    """

    def __init__(
        self,
        cloud_name: str,
        api_key: str,
        api_secret: str,
        folder: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._cloud_name = cloud_name
        self._api_key = api_key
        self._api_secret = api_secret
        self._folder = folder
        self._client = client or httpx.Client()

    def save(self, content: bytes, content_type: str) -> str:
        if content_type not in ACCEPTED_TYPES:
            raise PhotoRejected("A photo must be a JPEG, PNG or WebP image")
        if not content:
            raise PhotoRejected("The photo was empty")
        if len(content) > MAXIMUM_BYTES:
            raise PhotoRejected(f"A photo must be under {MAXIMUM_BYTES // (1024 * 1024)} MB")

        public_id = hashlib.sha256(content).hexdigest()[:32]
        timestamp = str(int(time.time()))
        signed = {
            "folder": self._folder,
            "public_id": public_id,
            "timestamp": timestamp,
        }

        try:
            response = self._client.post(
                f"https://api.cloudinary.com/v1_1/{self._cloud_name}/image/upload",
                data={
                    **signed,
                    "api_key": self._api_key,
                    "signature": self._signature(signed),
                },
                files={"file": ("report", content, content_type)},
                timeout=UPLOAD_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            url = response.json().get("secure_url")
        except httpx.HTTPError as error:
            raise PhotoRejected(
                "The photo could not be stored. Try again when you have a better signal."
            ) from error

        if not isinstance(url, str) or not url:
            raise PhotoRejected("The photo store did not return a usable address.")
        return url

    def find(self, reference: str) -> Path | None:
        """Nothing is held locally. A Cloudinary reference is already a URL the
        client fetches directly, so there is no file for this server to serve."""
        _ = reference
        return None

    def _signature(self, params: dict[str, str]) -> str:
        payload = "&".join(f"{key}={params[key]}" for key in sorted(params))
        return hashlib.sha1(f"{payload}{self._api_secret}".encode()).hexdigest()
