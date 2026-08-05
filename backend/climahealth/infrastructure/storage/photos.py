import hashlib
from pathlib import Path

ACCEPTED_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAXIMUM_BYTES = 6 * 1024 * 1024


class PhotoRejected(ValueError):
    pass


class LocalPhotoStore:
    """Report photographs on disk, addressed by the hash of their contents.

    Content addressing means the same photograph submitted twice costs one file, and a
    reference cannot be guessed from a report id. Local disk is the right weight for a
    single deployment; the interface is small enough that object storage is a swap.
    """

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, content_type: str) -> str:
        if content_type not in ACCEPTED_TYPES:
            raise PhotoRejected(
                "A photo must be a JPEG, PNG or WebP image",
            )
        if not content:
            raise PhotoRejected("The photo was empty")
        if len(content) > MAXIMUM_BYTES:
            raise PhotoRejected(f"A photo must be under {MAXIMUM_BYTES // (1024 * 1024)} MB")

        digest = hashlib.sha256(content).hexdigest()[:32]
        reference = f"{digest}{ACCEPTED_TYPES[content_type]}"
        path = self._directory / reference
        if not path.exists():
            path.write_bytes(content)
        return reference

    def find(self, reference: str) -> Path | None:
        # A reference is a filename we generated, never a path the caller supplies.
        if "/" in reference or "\\" in reference or ".." in reference:
            return None
        path = self._directory / reference
        return path if path.is_file() else None
