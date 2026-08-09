from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

import asyncpg

from app.domain import TicketSearchCriteria, TripSchedule
from app.errors import (
    BookingConflictError,
    BookingForbiddenError,
    BookingNotFoundError,
    BookingValidationError,
    BusImportValidationError,
    InvalidAccessTokenError,
    InvalidCredentialError,
    ReportValidationError,
    TripConflictError,
    TripNotFoundError,
    TripValidationError,
)
from app.repository import (
    count_passenger_bookings_today,
    credit_wallet,
    debit_wallet,
    get_available_routes,
    get_available_tickets,
    get_booking_context,
    get_booking_for_cancellation,
    get_buses,
    get_busiest_drivers_report,
    get_drivers,
    get_hourly_booking_report,
    get_monthly_bus_report,
    get_operator_trips,
    get_trip_creation_context,
    get_trip_schedule_conflicts,
    get_trip_seat_map,
    get_user_bookings,
    get_user_by_mobile,
    get_user_with_profiles,
    insert_booking_payment,
    insert_booking_refund,
    insert_confirmed_booking,
    insert_trip,
    mark_booking_cancelled,
    upsert_bus,
    upsert_route,
)
from app.schemas import (
    BookingCancellationResponse,
    BookingListItemResponse,
    BookingResponse,
    BusiestDriverReportRow,
    BusiestDriversReportResponse,
    BusImportItem,
    BusImportResponse,
    BusResponse,
    DriverResponse,
    HourlyBookingReportResponse,
    HourlyBookingReportRow,
    MonthlyBusReportResponse,
    MonthlyBusReportRow,
    OperatorTripResponse,
    RouteResponse,
    TicketQuery,
    TicketResponse,
    TripCreateRequest,
    TripResponse,
    TripSeatMapResponse,
)
from app.security import (
    TokenValidationError,
    create_access_token,
    decode_access_token,
    verify_password,
)

DAILY_BOOKING_LIMIT = 20
MIN_REPORT_YEAR = 2000
MAX_REPORT_YEAR = 2100


@dataclass(frozen=True)
class NormalizedBusImport:
    origin: str
    destination: str
    plate_number: str
    model: str | None
    capacity: int


async def authenticate_user(
    pool: asyncpg.Pool,
    mobile: str,
    password: str,
) -> str:
    user = await get_user_by_mobile(pool, mobile)

    if (
        user is None
        or not user["is_active"]
        or not verify_password(password, user["password_hash"])
    ):
        raise InvalidCredentialError()

    return create_access_token(user["id"])


async def resolve_access_token(pool: asyncpg.Pool, token: str) -> asyncpg.Record:
    try:
        user_id = decode_access_token(token)
    except TokenValidationError as err:
        raise InvalidAccessTokenError() from err

    user = await get_user_with_profiles(pool, user_id)

    if user is None or not user["is_active"]:
        raise InvalidAccessTokenError()

    return user


async def list_available_tickets(
    pool: asyncpg.Pool,
    query: TicketQuery,
) -> list[TicketResponse]:
    criteria = TicketSearchCriteria(
        origin=query.origin.strip() if query.origin else None,
        destination=query.destination.strip() if query.destination else None,
        sort=query.sort.value,
        limit=query.limit,
        offset=query.offset,
    )
    rows = await get_available_tickets(pool, criteria)

    return [TicketResponse(**dict(row)) for row in rows]


async def list_available_routes(pool: asyncpg.Pool) -> list[RouteResponse]:
    rows = await get_available_routes(pool)
    return [RouteResponse(**dict(row)) for row in rows]


async def get_trip_seats(
    pool: asyncpg.Pool,
    trip_id: int,
) -> TripSeatMapResponse:
    row = await get_trip_seat_map(pool, trip_id)

    if row is None:
        raise TripNotFoundError("Trip was not found")

    return TripSeatMapResponse(**dict(row))


async def create_booking(
    pool: asyncpg.Pool,
    user_id: int,
    trip_id: int,
    seat_number: int,
) -> BookingResponse:
    async with pool.acquire() as connection, connection.transaction():
        context = await get_booking_context(connection, user_id, trip_id)
        passenger_profile_id, trip = _require_booking_context(context)
        _validate_booking_availability(trip, seat_number)

        daily_count = await count_passenger_bookings_today(
            connection, passenger_profile_id
        )

        if daily_count >= DAILY_BOOKING_LIMIT:
            raise BookingConflictError("Daily booking limit has been reached")

        booking = await insert_confirmed_booking(
            connection=connection,
            passenger_profile_id=passenger_profile_id,
            trip_id=trip_id,
            seat_number=seat_number,
            paid_price=trip["price"],
        )

        if booking is None:
            raise BookingConflictError("Seat is already booked")

        remaining_balance = await debit_wallet(connection, user_id, trip["price"])

        if remaining_balance is None:
            raise BookingConflictError("Insufficient wallet balance")

        await insert_booking_payment(connection, user_id, booking["id"], trip["price"])

        return _booking_response(booking, remaining_balance)


def _require_booking_context(
    context: tuple[asyncpg.Record | None, int | None, asyncpg.Record | None],
) -> tuple[int, asyncpg.Record]:
    active_user, passenger_profile_id, trip = context
    if active_user is None:
        raise BookingForbiddenError("Active user was not found")
    if passenger_profile_id is None:
        raise BookingForbiddenError("Passenger profile is required")
    if trip is None:
        raise BookingNotFoundError("Trip was not found")
    return passenger_profile_id, trip


def _validate_booking_availability(trip: asyncpg.Record, seat_number: int) -> None:
    if trip["status"] != "scheduled" or trip["departure_time"] <= datetime.now(UTC):
        raise BookingConflictError("Trip is not available for booking")
    if seat_number > trip["capacity"]:
        raise BookingValidationError(
            f"Seat number must be between 1 and {trip['capacity']}"
        )
    if trip["confirmed_bookings"] >= trip["capacity"]:
        raise BookingConflictError("Trip is full")


def _booking_response(
    booking: asyncpg.Record,
    remaining_balance: Decimal,
) -> BookingResponse:
    return BookingResponse(
        id=booking["id"],
        trip_id=booking["trip_id"],
        seat_number=booking["seat_number"],
        paid_price=booking["paid_price"],
        status=booking["status"],
        booked_at=booking["booked_at"],
        remaining_wallet_balance=remaining_balance,
    )


async def cancel_booking(
    pool: asyncpg.Pool, user_id: int, booking_id: int
) -> BookingCancellationResponse:
    async with pool.acquire() as connection, connection.transaction():
        booking = await get_booking_for_cancellation(
            connection=connection, booking_id=booking_id, user_id=user_id
        )

        if booking is None:
            raise BookingNotFoundError("Booking was not found")

        if booking["status"] == "cancelled":
            return _cancellation_response(booking, booking["wallet_balance"])

        cancelled_booking = await mark_booking_cancelled(
            connection=connection, booking_id=booking_id
        )

        if cancelled_booking is None:
            raise BookingConflictError("Booking could not be cancelled")

        remaining_balance = await credit_wallet(
            connection=connection, user_id=user_id, amount=booking["paid_price"]
        )

        if remaining_balance is None:
            raise BookingConflictError("Wallet could not be credited")

        await insert_booking_refund(
            connection=connection,
            user_id=user_id,
            booking_id=booking_id,
            amount=booking["paid_price"],
        )

        return _cancellation_response(cancelled_booking, remaining_balance)


def _cancellation_response(
    booking: asyncpg.Record,
    remaining_balance: Decimal,
) -> BookingCancellationResponse:
    return BookingCancellationResponse(
        id=booking["id"],
        status=booking["status"],
        cancelled_at=booking["cancelled_at"],
        refunded_amount=booking["paid_price"],
        remaining_wallet_balance=remaining_balance,
    )


async def list_user_bookings(
    pool: asyncpg.Pool,
    user_id: int,
) -> list[BookingListItemResponse]:
    rows = await get_user_bookings(pool, user_id)
    return [BookingListItemResponse(**dict(row)) for row in rows]


async def import_buses(
    pool: asyncpg.Pool,
    buses: list[BusImportItem],
) -> BusImportResponse:
    imported_buses: list[BusResponse] = []

    async with pool.acquire() as connection, connection.transaction():
        for bus in map(_normalize_bus_import, buses):
            route_id = await upsert_route(
                connection=connection,
                origin=bus.origin,
                destination=bus.destination,
            )

            imported_bus = await upsert_bus(
                connection=connection,
                route_id=route_id,
                plate_number=bus.plate_number,
                model=bus.model,
                capacity=bus.capacity,
            )

            imported_buses.append(BusResponse(**dict(imported_bus)))

        return BusImportResponse(
            imported_count=len(imported_buses), buses=imported_buses
        )


def _normalize_bus_import(bus: BusImportItem) -> NormalizedBusImport:
    normalized = NormalizedBusImport(
        origin=bus.origin.strip(),
        destination=bus.destination.strip(),
        plate_number=bus.plate_number.strip(),
        model=bus.model.strip() if bus.model else None,
        capacity=bus.capacity,
    )
    if len(normalized.origin) < 2 or len(normalized.destination) < 2:
        raise BusImportValidationError(
            "Origin and destination must contain at least two characters"
        )
    if normalized.origin.casefold() == normalized.destination.casefold():
        raise BusImportValidationError("Origin and destination must be different")
    if not normalized.plate_number:
        raise BusImportValidationError("Plate number must not be empty")
    return normalized


async def list_operator_buses(
    pool: asyncpg.Pool,
    limit: int,
    offset: int,
) -> list[BusResponse]:
    rows = await get_buses(pool, limit, offset)
    return [BusResponse(**dict(row)) for row in rows]


async def list_drivers(pool: asyncpg.Pool) -> list[DriverResponse]:
    rows = await get_drivers(pool)
    return [DriverResponse(**dict(row)) for row in rows]


async def list_operator_trips(
    pool: asyncpg.Pool,
    limit: int,
    offset: int,
) -> list[OperatorTripResponse]:
    rows = await get_operator_trips(pool, limit, offset)
    return [OperatorTripResponse(**dict(row)) for row in rows]


async def create_trip(
    pool: asyncpg.Pool,
    request: TripCreateRequest,
) -> TripResponse:
    normalized_departure, normalized_arrival = _normalize_trip_schedule(
        request.departure_time,
        request.arrival_time,
    )
    schedule = TripSchedule(
        bus_id=request.bus_id,
        driver_profile_id=request.driver_profile_id,
        departure_time=normalized_departure,
        arrival_time=normalized_arrival,
        price=request.price,
    )

    async with pool.acquire() as connection, connection.transaction():
        bus, driver = await get_trip_creation_context(
            connection=connection,
            bus_id=schedule.bus_id,
            driver_profile_id=schedule.driver_profile_id,
        )

        _require_trip_creation_context(bus, driver)

        conflicts = await get_trip_schedule_conflicts(connection, schedule)

        _validate_trip_conflicts(conflicts)

        trip = await insert_trip(connection, schedule)

        return TripResponse(**dict(trip))


def _normalize_trip_schedule(
    departure_time: datetime,
    arrival_time: datetime,
) -> tuple[datetime, datetime]:
    normalized_departure = _to_utc(departure_time, "Departure")
    normalized_arrival = _to_utc(arrival_time, "Arrival")

    if normalized_departure <= datetime.now(UTC):
        raise TripValidationError("Departure time must be in the future")
    if normalized_arrival <= normalized_departure:
        raise TripValidationError("Arrival time must be after departure time")
    return normalized_departure, normalized_arrival


def _to_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise TripValidationError(f"{field_name} time must include a timezone offset")
    return value.astimezone(UTC)


def _require_trip_creation_context(
    bus: asyncpg.Record | None,
    driver: asyncpg.Record | None,
) -> None:
    if bus is None:
        raise TripNotFoundError("Active bus was not found")
    if driver is None:
        raise TripNotFoundError("Active driver profile was not found")


def _validate_trip_conflicts(conflicts: asyncpg.Record) -> None:
    if conflicts["bus_has_conflict"]:
        raise TripConflictError("Bus already has an overlapping trip")
    if conflicts["driver_has_conflict"]:
        raise TripConflictError("Driver already has an overlapping trip")


async def build_hourly_booking_report(
    pool: asyncpg.Pool,
    report_date: date,
) -> HourlyBookingReportResponse:
    rows = await get_hourly_booking_report(pool, report_date)
    hours = [HourlyBookingReportRow(**dict(row)) for row in rows]

    return HourlyBookingReportResponse(
        report_date=report_date,
        total_confirmed_bookings=sum(row.confirmed_bookings for row in hours),
        total_revenue=sum((row.revenue for row in hours), Decimal("0.00")),
        hours=hours,
    )


async def build_monthly_bus_report(
    pool: asyncpg.Pool,
    year: int,
    month: int,
) -> MonthlyBusReportResponse:
    if year < MIN_REPORT_YEAR or year > MAX_REPORT_YEAR:
        raise ReportValidationError(
            f"Year must be between {MIN_REPORT_YEAR} and {MAX_REPORT_YEAR}"
        )

    if month < 1 or month > 12:
        raise ReportValidationError("Month must be between 1 and 12")

    rows = await get_monthly_bus_report(pool, year, month)

    return MonthlyBusReportResponse(
        year=year,
        month=month,
        buses=[MonthlyBusReportRow(**dict(row)) for row in rows],
    )


async def build_busiest_drivers_report(
    pool: asyncpg.Pool,
    date_from: date,
    date_to: date,
    limit: int,
) -> BusiestDriversReportResponse:
    if date_to < date_from:
        raise ReportValidationError("date_to must not be before date_from")

    rows = await get_busiest_drivers_report(pool, date_from, date_to, limit)

    return BusiestDriversReportResponse(
        date_from=date_from,
        date_to=date_to,
        drivers=[BusiestDriverReportRow(**dict(row)) for row in rows],
    )
