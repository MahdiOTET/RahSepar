from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import settings

password_hasher = PasswordHash.recommended()

JWT_ALGORITHM = "HS256"
TOKEN_LIFETIME = timedelta(hours=1)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return password_hasher.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    issued_at = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": issued_at + TOKEN_LIFETIME,
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


class TokenValidationError(Exception):
    pass


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )
        user_id = int(payload["sub"])

        if user_id <= 0:
            raise ValueError("Invalid user ID")

        return user_id

    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as err:
        raise TokenValidationError() from err
