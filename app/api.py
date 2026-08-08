import asyncpg
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.db import get_pool
from app.schemas import (
    LoginRequest,
    TokenResponse,
    CurrentUserResponse,
    TicketResponse,
    TicketSort,
    BookingCreateRequest,
    BookingResponse,
    BookingCancellationResponse,
)
from app.service import (
    InvalidCredentialError,
    InvalidAccessTokenError,
    BookingForbiddenError,
    BookingNotFoundError,
    BookingValidationError,
    BookingConflictError,
    list_available_tickets,
    authenticate_user,
    resolve_access_token,
    create_booking,
    cancel_booking,
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


@router.get("/tickets", response_model=list[TicketResponse])
async def list_tickets(
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    origin: Annotated[str | None, Query(min_length=2, max_length=100)] = None,
    destination: Annotated[str | None, Query(min_length=2, max_length=100)] = None,
    sort: TicketSort = TicketSort.PRICE_ASC,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TicketResponse]:
    return await list_available_tickets(
        pool=pool,
        origin=origin,
        destination=destination,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def book_trip(
    request_data: BookingCreateRequest,
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    user: Annotated[CurrentUserResponse, Depends(get_current_user)],
) -> BookingResponse:
    try:
        return await create_booking(
            pool=pool,
            user_id=user.id,
            trip_id=request_data.trip_id,
            seat_number=request_data.seat_number,
        )

    except BookingForbiddenError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(err)
        ) from err

    except BookingNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
        ) from err

    except BookingValidationError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(err)
        ) from err

    except BookingConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(err)
        ) from err


@router.delete("/bookings/{booking_id}", response_model=BookingCancellationResponse)
async def cancel_existing_booking(
    booking_id: Annotated[int, Path(gt=0)],
    pool: Annotated[asyncpg.Pool, Depends(get_pool)],
    user: Annotated[CurrentUserResponse, Depends(get_current_user)],
) -> BookingCancellationResponse:
    try:
        return await cancel_booking(pool=pool, user_id=user.id, booking_id=booking_id)

    except BookingNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err

    except BookingConflictError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
