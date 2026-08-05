import hashlib
import hmac
import secrets

HASH_ALGORITHM = "sha256"
ITERATIONS = 200_000
SALT_BYTES = 16


class Pbkdf2PasswordHasher:
    def __init__(self, iterations: int = ITERATIONS) -> None:
        self._iterations = iterations

    def hash(self, password: str, salt: str) -> str:
        derived = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode("utf-8"),
            bytes.fromhex(salt),
            self._iterations,
        )
        return derived.hex()

    def verify(self, password: str, salt: str, expected_hash: str) -> bool:
        return hmac.compare_digest(self.hash(password, salt), expected_hash)


def generate_salt() -> str:
    return secrets.token_hex(SALT_BYTES)
