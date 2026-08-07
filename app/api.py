import asyncpg
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from app.db import get_pool
from app.schemas import LoginRequest, TokenResponse
from app.service import InvalidCredentialError, authenticate_user

router = APIRouter()


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
