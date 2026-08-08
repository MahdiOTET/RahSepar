import asyncpg

from app.repository import get_user_by_mobile, get_user_with_profiles
from app.security import (
    create_access_token,
    verify_password,
    TokenValidationError,
    decode_access_token,
)


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


class InvalidAccessTokenError(Exception):
    pass


async def resolve_access_token(pool: asyncpg.Pool, token: str) -> asyncpg.Record:
    try:
        user_id = decode_access_token(token)

    except TokenValidationError as err:
        raise InvalidAccessTokenError() from err

    user = await get_user_with_profiles(pool, user_id)

    if user is None or not user["is_active"]:
        raise InvalidAccessTokenError()

    return user
