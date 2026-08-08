import asyncpg
from datetime import UTC, datetime

from app.repository import (
    get_user_by_mobile,
    get_user_with_profiles,
    get_available_tickets,
    get_booking_context,
    insert_booking_payment,
    insert_confirmed_booking,
    debit_wallet,
    count_passenger_bookings_today,
    get_booking_for_cancellation,
    mark_booking_cancelled,
    credit_wallet,
    insert_booking_refund,
    upsert_route,
    upsert_bus,
)
from app.security import (
    create_access_token,
    verify_password,
    TokenValidationError,
    decode_access_token,
)
from app.schemas import (
    TicketResponse,
    TicketSort,
    BookingResponse,
    BookingCancellationResponse,
    BusResponse,
    BusImportItem,
    BusImportResponse,
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


async def list_available_tickets(
    pool: asyncpg.Pool,
    origin: str | None,
    destination: str | None,
    sort: TicketSort,
    limit: int,
    offset: int,
) -> list[TicketResponse]:
    rows = await get_available_tickets(
        pool=pool,
        origin=origin.strip() if origin else None,
        destination=destination.strip() if destination else None,
        sort=sort.value,
        limit=limit,
        offset=offset,
    )

    return [TicketResponse(**dict(row)) for row in rows]


class BookingForbiddenError(Exception):
    pass


class BookingNotFoundError(Exception):
    pass


class BookingValidationError(Exception):
    pass


class BookingConflictError(Exception):
    pass


async def create_booking(
    pool: asyncpg.Pool,
    user_id: int,
    trip_id: int,
    seat_number: int,
) -> BookingResponse:
    async with pool.acquire() as connection:
        async with connection.transaction():
            user, passenger_profile_id, trip = await get_booking_context(
                connection, user_id, trip_id
            )

            if user is None:
                raise BookingForbiddenError("Active user was not found")

            if passenger_profile_id is None:
                raise BookingForbiddenError("Passenger profile is required")

            if trip is None:
                raise BookingNotFoundError("Trip was not found")

            if trip["status"] != "scheduled" or trip["departure_time"] <= datetime.now(
                UTC
            ):
                raise BookingConflictError("Trip is not available for booking")

            if seat_number > trip["capacity"]:
                raise BookingValidationError(
                    f"Seat number must be between 1 and {trip['capacity']}"
                )

            daily_count = await count_passenger_bookings_today(
                connection, passenger_profile_id
            )

            if daily_count >= 20:
                raise BookingConflictError("Daily booking limit has been reached")

            if trip["confirmed_bookings"] >= trip["capacity"]:
                raise BookingConflictError("Trip is full")

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

            await insert_booking_payment(
                connection, user_id, booking["id"], trip["price"]
            )

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
    async with pool.acquire() as connection:
        async with connection.transaction():
            booking = await get_booking_for_cancellation(
                connection=connection, booking_id=booking_id, user_id=user_id
            )

            if booking is None:
                raise BookingNotFoundError("Booking was not found")

            if booking["status"] == "cancelled":
                return BookingCancellationResponse(
                    id=booking["id"],
                    status=booking["status"],
                    cancelled_at=booking["cancelled_at"],
                    refunded_amount=booking["paid_price"],
                    remaining_wallet_balance=booking["wallet_balance"],
                )

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

            return BookingCancellationResponse(
                id=cancelled_booking["id"],
                status=cancelled_booking["status"],
                cancelled_at=cancelled_booking["cancelled_at"],
                refunded_amount=cancelled_booking["paid_price"],
                remaining_wallet_balance=remaining_balance,
            )


class BusImportValidationError(Exception):
    pass


async def import_buses(
    pool: asyncpg.Pool,
    buses: list[BusImportItem],
) -> BusImportResponse:
    imported_buses: list[BusResponse] = []

    async with pool.acquire() as connection:
        async with connection.transaction():
            for bus in buses:
                origin = bus.origin.strip()
                destination = bus.destination.strip()
                plate_number = bus.plate_number.strip()
                model = bus.model.strip() if bus.model else None

                if len(origin) < 2 or len(destination) < 2:
                    raise BusImportValidationError(
                        "Origin and destination must contain at least two characters"
                    )

                if origin.casefold() == destination.casefold():
                    raise BusImportValidationError(
                        "Origin and destination must be different"
                    )

                if not plate_number:
                    raise BusImportValidationError("Plate number must not be empty")

                route_id = await upsert_route(
                    connection=connection, origin=origin, destination=destination
                )

                imported_bus = await upsert_bus(
                    connection=connection,
                    route_id=route_id,
                    plate_number=plate_number,
                    model=model,
                    capacity=bus.capacity,
                )

                imported_buses.append(BusResponse(**dict(imported_bus)))

            return BusImportResponse(
                imported_count=len(imported_buses), buses=imported_buses
            )
