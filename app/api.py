from datetime import date
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db import get_pool
from app.schemas import (
    BookingCancellationResponse,
    BookingCreateRequest,
    BookingListItemResponse,
    BookingResponse,
    BusiestDriversReportResponse,
    BusImportRequest,
    BusImportResponse,
    BusResponse,
    CurrentUserResponse,
    DriverResponse,
    HourlyBookingReportResponse,
    LoginRequest,
    MonthlyBusReportResponse,
    OperatorTripResponse,
    RouteResponse,
    TicketQuery,
    TicketResponse,
    TokenResponse,
    TripCreateRequest,
    TripResponse,
    TripSeatMapResponse,
)
from app.service import (
    authenticate_user,
    build_busiest_drivers_report,
    build_hourly_booking_report,
    build_monthly_bus_report,
    cancel_booking,
    create_booking,
    create_trip,
    get_trip_seats,
    import_buses,
    list_available_routes,
    list_available_tickets,
    list_drivers,
    list_operator_buses,
    list_operator_trips,
    list_user_bookings,
    resolve_access_token,
)

router = APIRouter()

bearer_schema = HTTPBearer(auto_error=False)
DatabasePool = Annotated[asyncpg.Pool, Depends(get_pool)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_schema),
]


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    requested_data: LoginRequest,
    pool: DatabasePool,
) -> TokenResponse:
    token = await authenticate_user(
        pool, requested_data.mobile, requested_data.password
    )
    return TokenResponse(access_token=token)


async def get_current_user(
    credentials: BearerCredentials,
    pool: DatabasePool,
) -> CurrentUserResponse:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await resolve_access_token(pool, credentials.credentials)

    return CurrentUserResponse(
        id=user["id"],
        mobile=user["mobile"],
        display_name=user["display_name"],
        wallet_balance=user["wallet_balance"],
        profiles=list(user["profiles"]),
    )


AuthenticatedUser = Annotated[CurrentUserResponse, Depends(get_current_user)]


@router.get("/users/me", response_model=CurrentUserResponse)
async def current_user(
    user: AuthenticatedUser,
) -> CurrentUserResponse:
    return user


@router.get("/tickets", response_model=list[TicketResponse])
async def list_tickets(
    pool: DatabasePool,
    query: Annotated[TicketQuery, Query()],
) -> list[TicketResponse]:
    return await list_available_tickets(pool, query)


@router.get("/routes", response_model=list[RouteResponse])
async def list_routes(
    pool: DatabasePool,
) -> list[RouteResponse]:
    return await list_available_routes(pool)


@router.get("/trips/{trip_id}/seats", response_model=TripSeatMapResponse)
async def trip_seats(
    trip_id: Annotated[int, Path(gt=0)],
    pool: DatabasePool,
) -> TripSeatMapResponse:
    return await get_trip_seats(pool, trip_id)


@router.get("/bookings", response_model=list[BookingListItemResponse])
async def list_my_bookings(
    pool: DatabasePool,
    user: AuthenticatedUser,
) -> list[BookingListItemResponse]:
    return await list_user_bookings(pool, user.id)


@router.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def book_trip(
    request_data: BookingCreateRequest,
    pool: DatabasePool,
    user: AuthenticatedUser,
) -> BookingResponse:
    return await create_booking(
        pool=pool,
        user_id=user.id,
        trip_id=request_data.trip_id,
        seat_number=request_data.seat_number,
    )


@router.delete("/bookings/{booking_id}", response_model=BookingCancellationResponse)
async def cancel_existing_booking(
    booking_id: Annotated[int, Path(gt=0)],
    pool: DatabasePool,
    user: AuthenticatedUser,
) -> BookingCancellationResponse:
    return await cancel_booking(pool=pool, user_id=user.id, booking_id=booking_id)


async def require_operator(
    user: AuthenticatedUser,
) -> CurrentUserResponse:
    if "operator" not in user.profiles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Operator profile is required"
        )

    return user


OperatorUser = Annotated[CurrentUserResponse, Depends(require_operator)]


@router.get("/buses", response_model=list[BusResponse])
async def list_buses(
    pool: DatabasePool,
    _operator: OperatorUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[BusResponse]:
    return await list_operator_buses(pool, limit, offset)


@router.get("/drivers", response_model=list[DriverResponse])
async def list_driver_profiles(
    pool: DatabasePool,
    _operator: OperatorUser,
) -> list[DriverResponse]:
    return await list_drivers(pool)


@router.get("/trips", response_model=list[OperatorTripResponse])
async def list_scheduled_trips(
    pool: DatabasePool,
    _operator: OperatorUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[OperatorTripResponse]:
    return await list_operator_trips(pool, limit, offset)


@router.post(
    "/buses", response_model=BusImportResponse, status_code=status.HTTP_201_CREATED
)
async def bulk_import_buses(
    request_data: BusImportRequest,
    pool: DatabasePool,
    _operator: OperatorUser,
) -> BusImportResponse:
    return await import_buses(pool=pool, buses=request_data.buses)


@router.post(
    "/trips",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scheduled_trip(
    request_data: TripCreateRequest,
    pool: DatabasePool,
    _operator: OperatorUser,
) -> TripResponse:
    return await create_trip(pool, request_data)


@router.get(
    "/reports/hourly-bookings",
    response_model=HourlyBookingReportResponse,
)
async def hourly_booking_report(
    report_date: date,
    pool: DatabasePool,
    _operator: OperatorUser,
) -> HourlyBookingReportResponse:
    return await build_hourly_booking_report(pool, report_date)


@router.get(
    "/reports/monthly-buses",
    response_model=MonthlyBusReportResponse,
)
async def monthly_bus_report(
    year: Annotated[int, Query(ge=2000, le=2100)],
    month: Annotated[int, Query(ge=1, le=12)],
    pool: DatabasePool,
    _operator: OperatorUser,
) -> MonthlyBusReportResponse:
    return await build_monthly_bus_report(pool, year, month)


@router.get(
    "/reports/busiest-drivers",
    response_model=BusiestDriversReportResponse,
)
async def busiest_drivers_report(
    date_from: date,
    date_to: date,
    pool: DatabasePool,
    _operator: OperatorUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> BusiestDriversReportResponse:
    return await build_busiest_drivers_report(
        pool=pool,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
