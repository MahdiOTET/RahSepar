import asyncpg
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.db import get_pool
from app.schemas import LoginRequest, TokenResponse, CurrentUserResponse
from app.service import (
    InvalidCredentialError,
    InvalidAccessTokenError,
    authenticate_user,
    resolve_access_token,
)

router = APIRouter()

bearer_schema = HTTPBearer(auto_error=False)


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    requested_data: LoginRequest, pool: Annotated[asyncpg.Pool, Depends(get_pool)]
) -> TokenResponse:
    try:
        token = await authenticate_user(
            pool, requested_data.mobile, requested_data.password
        )
    except InvalidCredentialError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Mobile or Password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    return TokenResponse(access_token=token)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_schema)],
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
) -> CurrentUserResponse:

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await resolve_access_token(pool, credentials.credentials)

    except InvalidAccessTokenError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    return CurrentUserResponse(
        id=user["id"], mobile=user["mobile"], profiles=list(user["profiles"])
    )


@router.get("/users/me", response_model=CurrentUserResponse)
async def current_user(
    user: Annotated[CurrentUserResponse, Depends(get_current_user)],
) -> CurrentUserResponse:
    return user
