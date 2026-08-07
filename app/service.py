import asyncpg

from app.repository import get_user_by_mobile
from app.security import create_access_token, verify_password


class InvalidCredentialError(Exception):
    pass


async def authenticate_user(
    pool: asyncpg.Pool,
    mobile: str,
    password: str,
) -> str:

    user = await get_user_by_mobile(pool, mobile)

    if user is None or not user["is_active"]:
        raise InvalidCredentialError()

    password_is_valid = verify_password(password, user["password_hash"])

    if not password_is_valid:
        raise InvalidCredentialError()

    return create_access_token(user["id"])
