from pwdlib import PasswordHash
from datetime import UTC, datetime, timedelta
from app.config import settings
import jwt

pass_hasher = PasswordHash.recommended()

JWT_ALGORITHM = "HS256"
TOKEN_LIFETIME = timedelta(hours=1)


def hash_password(pwd: str) -> str:
    return pass_hasher.hash(pwd)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return pass_hasher.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    issued_at = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": issued_at + TOKEN_LIFETIME,
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)
