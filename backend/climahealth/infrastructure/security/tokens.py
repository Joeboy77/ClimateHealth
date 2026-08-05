from datetime import UTC, datetime, timedelta

import jwt

from climahealth.services.access import (
    Agency,
    AuthenticatedUser,
    InvalidToken,
    Scope,
    ScopeLevel,
    UserRole,
)

TOKEN_ALGORITHM = "HS256"
TOKEN_LIFETIME_HOURS = 12
MINIMUM_SECRET_LENGTH = 32


class WeakTokenSecret(ValueError):
    pass


class JwtTokenIssuer:
    def __init__(
        self,
        secret: str,
        lifetime: timedelta = timedelta(hours=TOKEN_LIFETIME_HOURS),
    ) -> None:
        if len(secret.encode("utf-8")) < MINIMUM_SECRET_LENGTH:
            raise WeakTokenSecret(
                f"Token secret must be at least {MINIMUM_SECRET_LENGTH} bytes for HS256"
            )
        self._secret = secret
        self._lifetime = lifetime

    def issue(self, user: AuthenticatedUser) -> str:
        issued_at = datetime.now(UTC)
        payload = {
            "sub": user.user_id,
            "username": user.username,
            "display_name": user.display_name,
            "job_title": user.job_title,
            "agency": user.agency.value,
            "role": user.role.value,
            "scope_level": user.scope.level.value,
            "district_id": user.scope.district_id,
            "iat": issued_at,
            "exp": issued_at + self._lifetime,
        }
        return jwt.encode(payload, self._secret, algorithm=TOKEN_ALGORITHM)

    def decode(self, token: str) -> AuthenticatedUser:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[TOKEN_ALGORITHM])
        except jwt.PyJWTError as error:
            raise InvalidToken(f"Could not validate credentials: {error}") from error

        return AuthenticatedUser(
            user_id=payload["sub"],
            username=payload["username"],
            display_name=payload["display_name"],
            job_title=payload["job_title"],
            agency=Agency(payload["agency"]),
            role=UserRole(payload["role"]),
            scope=Scope(
                level=ScopeLevel(payload["scope_level"]),
                district_id=payload["district_id"],
            ),
        )
