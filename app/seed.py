from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import asyncpg

from app.config import settings
from app.domain import TripSchedule
from app.repository import (
    debit_wallet,
    insert_booking_payment,
    insert_confirmed_booking,
    upsert_bus,
    upsert_route,
)
from app.security import hash_password

DEV_PASSWORD = "DevPass123!"
BULK_BOOKING_PRICE = Decimal("1000000.00")
BULK_INITIAL_CREDIT = Decimal("50000000.00")
BULK_BUS_COUNT = 20
BULK_DRIVER_COUNT = 20
BULK_BUS_CAPACITY = 100
BULK_DAILY_BOOKING_LIMIT = 20
OPERATOR_MOBILE = "09123456789"
DRIVER_MOBILE = "09120000002"
PRIMARY_TICKET_PRICE = Decimal("1000000.00")
PRIMARY_WALLET_CREDIT = Decimal("10000000.00")

BULK_ROUTES = (
    ("تهران", "مشهد"),
    ("مشهد", "تهران"),
    ("شیراز", "تهران"),
    ("تهران", "اصفهان"),
    ("اصفهان", "تهران"),
)


@dataclass(frozen=True)
class DemoRoute:
    origin: str
    destination: str
    bus_model: str
    base_price: Decimal
    duration_hours: int


DEMO_ROUTES = (
    DemoRoute("تهران", "شیراز", "Volvo B9R", Decimal("950000.00"), 10),
    DemoRoute("تهران", "مشهد", "Scania Maral", Decimal("1250000.00"), 12),
    DemoRoute("مشهد", "تهران", "Volvo B11R", Decimal("1200000.00"), 12),
    DemoRoute("شیراز", "تهران", "Scania Classic", Decimal("900000.00"), 10),
    DemoRoute("تهران", "اصفهان", "MAN Lion's Coach", Decimal("720000.00"), 6),
    DemoRoute("اصفهان", "تهران", "Volvo B9R", Decimal("680000.00"), 6),
)


@dataclass(frozen=True)
class SeededDemoAccounts:
    operator_user_id: int
    passenger_profile_id: int
    driver_profile_id: int


async def _upsert_user(
    connection: asyncpg.Connection,
    mobile: str,
    hashed_password: str,
) -> int:
    return await connection.fetchval(
        """
        INSERT INTO users (mobile, password_hash)
        VALUES ($1, $2)
        ON CONFLICT (mobile)
        DO UPDATE SET
            password_hash = EXCLUDED.password_hash,
            is_active = TRUE
        RETURNING id
        """,
        mobile,
        hashed_password,
    )


async def _upsert_profile(
    connection: asyncpg.Connection,
    user_id: int,
    display_name: str,
    profile_type: str,
) -> int:
    return await connection.fetchval(
        """
        INSERT INTO profiles (
            user_id,
            display_name,
            profile_type
        )
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id, profile_type)
        DO UPDATE SET
            display_name = EXCLUDED.display_name
        RETURNING id
        """,
        user_id,
        display_name,
        profile_type,
    )


def _validate_bulk_booking_count(booking_count: int) -> None:
    if booking_count < 0:
        raise ValueError("booking_count must not be negative")
    if booking_count > 1_000_000:
        raise ValueError("booking_count must not exceed 1,000,000")


def _required_records(item_count: int, capacity: int) -> int:
    return (item_count + capacity - 1) // capacity


async def _seed_bulk_infrastructure(
    connection: asyncpg.Connection,
    hashed_password: str,
) -> tuple[list[int], list[int]]:
    driver_profile_ids: list[int] = []
    for number in range(1, BULK_DRIVER_COUNT + 1):
        driver_user_id = await _upsert_user(
            connection=connection,
            mobile=f"097{number:08d}",
            hashed_password=hashed_password,
        )
        driver_profile_ids.append(
            await _upsert_profile(
                connection=connection,
                user_id=driver_user_id,
                display_name=f"راننده آزمایشی {number}",
                profile_type="driver",
            )
        )

    route_ids = [
        await upsert_route(
            connection=connection,
            origin=origin,
            destination=destination,
        )
        for origin, destination in BULK_ROUTES
    ]
    bus_ids: list[int] = []
    for number in range(1, BULK_BUS_COUNT + 1):
        bus = await upsert_bus(
            connection=connection,
            route_id=route_ids[(number - 1) % len(route_ids)],
            plate_number=f"LOAD-{number:03d}",
            model="اتوبوس داده آزمایشی",
            capacity=BULK_BUS_CAPACITY,
        )
        bus_ids.append(bus["id"])

    return driver_profile_ids, bus_ids


async def _seed_bulk_passengers(
    connection: asyncpg.Connection,
    hashed_password: str,
    passenger_count: int,
) -> list[asyncpg.Record]:
    await connection.execute(
        """
            CREATE TEMP TABLE seed_passenger_data (
                seed_number INTEGER PRIMARY KEY,
                mobile VARCHAR(15) NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                booked_at TIMESTAMPTZ NOT NULL
            ) ON COMMIT DROP
        """
    )
    booking_anchor = datetime(2026, 1, 1, tzinfo=UTC)
    passenger_records = [
        (
            number,
            f"098{number:08d}",
            "مسافر نمایشی" if number == 1 else f"Load Passenger {number}",
            booking_anchor + timedelta(days=(number - 1) % 30, hours=(number - 1) % 24),
        )
        for number in range(1, passenger_count + 1)
    ]
    await connection.copy_records_to_table(
        "seed_passenger_data",
        records=passenger_records,
        columns=["seed_number", "mobile", "display_name", "booked_at"],
    )
    await connection.execute(
        """
            INSERT INTO users (
                mobile,
                password_hash,
                wallet_balance
            )
            SELECT
                seed.mobile,
                $1,
                $2
            FROM seed_passenger_data AS seed
            ON CONFLICT (mobile)
            DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                is_active = TRUE
        """,
        hashed_password,
        BULK_INITIAL_CREDIT,
    )
    await connection.execute(
        """
            INSERT INTO profiles (
                user_id,
                display_name,
                profile_type
            )
            SELECT
                app_user.id,
                seed.display_name,
                'passenger'
            FROM seed_passenger_data AS seed
            JOIN users AS app_user
                ON app_user.mobile = seed.mobile
            ON CONFLICT (user_id, profile_type)
            DO UPDATE SET
                display_name = EXCLUDED.display_name
        """
    )
    return await connection.fetch(
        """
            SELECT
                seed.seed_number,
                profile.id AS passenger_profile_id,
                app_user.id AS user_id,
                seed.booked_at
            FROM seed_passenger_data AS seed
            JOIN users AS app_user
                ON app_user.mobile = seed.mobile
            JOIN profiles AS profile
                ON profile.user_id = app_user.id
                AND profile.profile_type = 'passenger'
            ORDER BY seed.seed_number
        """
    )


async def _seed_bulk_trips(
    connection: asyncpg.Connection,
    bus_ids: list[int],
    driver_profile_ids: list[int],
    trip_count: int,
) -> list[asyncpg.Record]:
    await connection.execute(
        """
            CREATE TEMP TABLE seed_trip_data (
                seed_number INTEGER PRIMARY KEY,
                bus_id BIGINT NOT NULL,
                driver_profile_id BIGINT NOT NULL,
                departure_time TIMESTAMPTZ NOT NULL,
                arrival_time TIMESTAMPTZ NOT NULL,
                price NUMERIC(12, 2) NOT NULL
            ) ON COMMIT DROP
        """
    )
    trip_anchor = datetime(2035, 1, 1, tzinfo=UTC)
    trip_records = [
        (
            number,
            bus_ids[(number - 1) % len(bus_ids)],
            driver_profile_ids[(number - 1) % len(driver_profile_ids)],
            trip_anchor + timedelta(hours=(number - 1) * 12),
            trip_anchor + timedelta(hours=(number - 1) * 12 + 8),
            BULK_BOOKING_PRICE,
        )
        for number in range(1, trip_count + 1)
    ]
    await connection.copy_records_to_table(
        "seed_trip_data",
        records=trip_records,
        columns=[
            "seed_number",
            "bus_id",
            "driver_profile_id",
            "departure_time",
            "arrival_time",
            "price",
        ],
    )
    await connection.execute(
        """
            INSERT INTO trips (
                bus_id,
                driver_profile_id,
                departure_time,
                arrival_time,
                price
            )
            SELECT
                seed.bus_id,
                seed.driver_profile_id,
                seed.departure_time,
                seed.arrival_time,
                seed.price
            FROM seed_trip_data AS seed
            WHERE NOT EXISTS (
                SELECT 1
                FROM trips AS existing_trip
                WHERE existing_trip.bus_id = seed.bus_id
                  AND existing_trip.driver_profile_id = seed.driver_profile_id
                  AND existing_trip.departure_time = seed.departure_time
            )
        """
    )
    return await connection.fetch(
        """
            SELECT DISTINCT ON (seed.seed_number)
                seed.seed_number,
                trip.id AS trip_id
            FROM seed_trip_data AS seed
            JOIN trips AS trip
                ON trip.bus_id = seed.bus_id
                AND trip.driver_profile_id = seed.driver_profile_id
                AND trip.departure_time = seed.departure_time
            ORDER BY seed.seed_number, trip.id
        """
    )


async def _seed_bulk_booking_history(
    connection: asyncpg.Connection,
    passenger_rows: list[asyncpg.Record],
    trip_rows: list[asyncpg.Record],
    booking_count: int,
) -> None:
    await connection.execute(
        """
            CREATE TEMP TABLE seed_booking_data (
                passenger_profile_id BIGINT NOT NULL,
                trip_id BIGINT NOT NULL,
                seat_number SMALLINT NOT NULL,
                paid_price NUMERIC(12, 2) NOT NULL,
                booked_at TIMESTAMPTZ NOT NULL
            ) ON COMMIT DROP
        """
    )
    booking_records = []
    for index in range(booking_count):
        passenger = passenger_rows[index % len(passenger_rows)]
        trip = trip_rows[index // BULK_BUS_CAPACITY]
        booking_records.append(
            (
                passenger["passenger_profile_id"],
                trip["trip_id"],
                index % BULK_BUS_CAPACITY + 1,
                BULK_BOOKING_PRICE,
                passenger["booked_at"],
            )
        )

    await connection.copy_records_to_table(
        "seed_booking_data",
        records=booking_records,
        columns=[
            "passenger_profile_id",
            "trip_id",
            "seat_number",
            "paid_price",
            "booked_at",
        ],
    )
    await connection.execute(
        """
            INSERT INTO bookings (
                passenger_profile_id,
                trip_id,
                seat_number,
                paid_price,
                booked_at
            )
            SELECT
                seed.passenger_profile_id,
                seed.trip_id,
                seed.seat_number,
                seed.paid_price,
                seed.booked_at
            FROM seed_booking_data AS seed
            ON CONFLICT (trip_id, seat_number)
                WHERE status = 'confirmed'
            DO UPDATE SET
                passenger_profile_id = EXCLUDED.passenger_profile_id,
                paid_price = EXCLUDED.paid_price,
                booked_at = EXCLUDED.booked_at
        """
    )
    await connection.execute(
        """
            INSERT INTO wallet_transactions (
                user_id,
                booking_id,
                transaction_type,
                amount
            )
            SELECT
                profile.user_id,
                booking.id,
                'booking_payment',
                seed.paid_price
            FROM seed_booking_data AS seed
            JOIN bookings AS booking
                ON booking.trip_id = seed.trip_id
                AND booking.seat_number = seed.seat_number
                AND booking.status = 'confirmed'
            JOIN profiles AS profile
                ON profile.id = seed.passenger_profile_id
            ON CONFLICT (booking_id, transaction_type)
            DO UPDATE SET
                user_id = EXCLUDED.user_id,
                amount = EXCLUDED.amount
        """
    )


async def _synchronize_bulk_wallets(connection: asyncpg.Connection) -> None:
    await connection.execute(
        """
            UPDATE wallet_transactions AS transaction
            SET amount = $1
            FROM users AS app_user
            JOIN seed_passenger_data AS seed
                ON seed.mobile = app_user.mobile
            WHERE transaction.user_id = app_user.id
              AND transaction.transaction_type = 'wallet_credit'
        """,
        BULK_INITIAL_CREDIT,
    )
    await connection.execute(
        """
            INSERT INTO wallet_transactions (
                user_id,
                transaction_type,
                amount
            )
            SELECT
                app_user.id,
                'wallet_credit',
                $1
            FROM seed_passenger_data AS seed
            JOIN users AS app_user
                ON app_user.mobile = seed.mobile
            WHERE NOT EXISTS (
                SELECT 1
                FROM wallet_transactions AS existing_credit
                WHERE existing_credit.user_id = app_user.id
                  AND existing_credit.transaction_type = 'wallet_credit'
            )
        """,
        BULK_INITIAL_CREDIT,
    )
    await connection.execute(
        """
            UPDATE users AS app_user
            SET wallet_balance = (
                $1
                - coalesce(
                    (
                        SELECT sum(transaction.amount)
                        FROM wallet_transactions AS transaction
                        WHERE transaction.user_id = app_user.id
                          AND transaction.transaction_type = 'booking_payment'
                    ),
                    0
                )
                + coalesce(
                    (
                        SELECT sum(transaction.amount)
                        FROM wallet_transactions AS transaction
                        WHERE transaction.user_id = app_user.id
                          AND transaction.transaction_type = 'booking_refund'
                    ),
                    0
                )
            )
            WHERE EXISTS (
                SELECT 1
                FROM seed_passenger_data AS seed
                WHERE seed.mobile = app_user.mobile
            )
        """,
        BULK_INITIAL_CREDIT,
    )


async def _count_bulk_bookings(connection: asyncpg.Connection) -> int:
    return await connection.fetchval(
        """
            SELECT count(*)
            FROM bookings AS booking
            JOIN profiles AS profile
                ON profile.id = booking.passenger_profile_id
            JOIN users AS app_user
                ON app_user.id = profile.user_id
            WHERE app_user.mobile LIKE '098%'
              AND booking.status = 'confirmed'
        """
    )


async def seed_bulk_bookings(
    connection: asyncpg.Connection,
    hashed_password: str,
    booking_count: int,
) -> int:
    _validate_bulk_booking_count(booking_count)
    if booking_count == 0:
        return 0

    passenger_count = _required_records(
        booking_count,
        BULK_DAILY_BOOKING_LIMIT,
    )
    trip_count = _required_records(booking_count, BULK_BUS_CAPACITY)
    driver_profile_ids, bus_ids = await _seed_bulk_infrastructure(
        connection,
        hashed_password,
    )
    passenger_rows = await _seed_bulk_passengers(
        connection,
        hashed_password,
        passenger_count,
    )
    trip_rows = await _seed_bulk_trips(
        connection,
        bus_ids,
        driver_profile_ids,
        trip_count,
    )
    await _seed_bulk_booking_history(
        connection,
        passenger_rows,
        trip_rows,
        booking_count,
    )
    await _synchronize_bulk_wallets(connection)
    return await _count_bulk_bookings(connection)


async def _get_active_demo_driver_ids(
    connection: asyncpg.Connection,
) -> list[int]:
    rows = await connection.fetch(
        """
            SELECT profile.id
            FROM profiles AS profile
            JOIN users AS app_user
                ON app_user.id = profile.user_id
            WHERE profile.profile_type = 'driver'
              AND app_user.is_active = TRUE
            ORDER BY profile.id
            LIMIT $1
        """,
        len(DEMO_ROUTES),
    )
    driver_ids = [row["id"] for row in rows]
    if len(driver_ids) < len(DEMO_ROUTES):
        raise RuntimeError("Not enough active drivers to seed available trips")
    return driver_ids


async def _get_reusable_trip_ids(
    connection: asyncpg.Connection,
    bus_id: int,
) -> list[int]:
    rows = await connection.fetch(
        """
            SELECT trip.id
            FROM trips AS trip
            WHERE trip.bus_id = $1
              AND NOT EXISTS (
                  SELECT 1
                  FROM bookings AS booking
                  WHERE booking.trip_id = trip.id
              )
            ORDER BY trip.id
            LIMIT 3
        """,
        bus_id,
    )
    return [row["id"] for row in rows]


async def _save_demo_trip(
    connection: asyncpg.Connection,
    schedule: TripSchedule,
    reusable_trip_id: int | None,
) -> int:
    if reusable_trip_id is not None:
        return await connection.fetchval(
            """
                UPDATE trips
                SET
                    driver_profile_id = $2,
                    departure_time = $3,
                    arrival_time = $4,
                    price = $5,
                    status = 'scheduled'
                WHERE id = $1
                RETURNING id
            """,
            reusable_trip_id,
            schedule.driver_profile_id,
            schedule.departure_time,
            schedule.arrival_time,
            schedule.price,
        )

    return await connection.fetchval(
        """
            INSERT INTO trips (
                bus_id,
                driver_profile_id,
                departure_time,
                arrival_time,
                price
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """,
        schedule.bus_id,
        schedule.driver_profile_id,
        schedule.departure_time,
        schedule.arrival_time,
        schedule.price,
    )


async def _seed_demo_route_trips(
    connection: asyncpg.Connection,
    route: DemoRoute,
    route_index: int,
    driver_profile_id: int,
    demo_anchor: datetime,
) -> int:
    route_id = await upsert_route(
        connection=connection,
        origin=route.origin,
        destination=route.destination,
    )
    bus = await upsert_bus(
        connection=connection,
        route_id=route_id,
        plate_number=f"RSP-{route_index + 1:03d}",
        model=route.bus_model,
        capacity=40,
    )
    bus_id = bus["id"]
    reusable_trip_ids = await _get_reusable_trip_ids(connection, bus_id)

    for slot in range(3):
        departure_time = demo_anchor + timedelta(
            days=2 + slot * 2,
            minutes=route_index * 20,
        )
        schedule = TripSchedule(
            bus_id=bus_id,
            driver_profile_id=driver_profile_id,
            departure_time=departure_time,
            arrival_time=departure_time + timedelta(hours=route.duration_hours),
            price=route.base_price + Decimal(slot * 125_000),
        )
        reusable_trip_id = (
            reusable_trip_ids[slot] if slot < len(reusable_trip_ids) else None
        )
        await _save_demo_trip(connection, schedule, reusable_trip_id)

    return 3


async def seed_available_demo_trips(connection: asyncpg.Connection) -> int:
    driver_ids = await _get_active_demo_driver_ids(connection)
    demo_anchor = datetime.now(UTC).replace(
        hour=5,
        minute=30,
        second=0,
        microsecond=0,
    )
    seeded_trip_count = 0
    for route_index, route in enumerate(DEMO_ROUTES):
        seeded_trip_count += await _seed_demo_route_trips(
            connection,
            route,
            route_index,
            driver_ids[route_index],
            demo_anchor,
        )

    return seeded_trip_count


async def _seed_primary_demo_accounts(
    connection: asyncpg.Connection,
    hashed_password: str,
) -> SeededDemoAccounts:
    operator_user_id = await _upsert_user(
        connection,
        OPERATOR_MOBILE,
        hashed_password,
    )
    passenger_profile_id = await _upsert_profile(
        connection,
        operator_user_id,
        "مسافر آزمایشی",
        "passenger",
    )
    await _upsert_profile(
        connection,
        operator_user_id,
        "مدیر آزمایشی",
        "operator",
    )

    driver_user_id = await _upsert_user(
        connection,
        DRIVER_MOBILE,
        hashed_password,
    )
    driver_profile_id = await _upsert_profile(
        connection,
        driver_user_id,
        "راننده آزمایشی اصلی",
        "driver",
    )
    return SeededDemoAccounts(
        operator_user_id=operator_user_id,
        passenger_profile_id=passenger_profile_id,
        driver_profile_id=driver_profile_id,
    )


async def _seed_primary_demo_trip(
    connection: asyncpg.Connection,
    driver_profile_id: int,
) -> int:
    route_id = await upsert_route(
        connection=connection,
        origin="تهران",
        destination="شیراز",
    )
    bus = await upsert_bus(
        connection=connection,
        route_id=route_id,
        plate_number="11A111-11",
        model="Volvo B9R",
        capacity=40,
    )
    bus_id = bus["id"]
    departure_time = datetime.now(UTC) + timedelta(days=1)
    trip_id = await connection.fetchval(
        """
        SELECT id
        FROM trips
        WHERE bus_id = $1
        ORDER BY id
        LIMIT 1
        """,
        bus_id,
    )
    schedule = TripSchedule(
        bus_id=bus_id,
        driver_profile_id=driver_profile_id,
        departure_time=departure_time,
        arrival_time=departure_time + timedelta(hours=10),
        price=PRIMARY_TICKET_PRICE,
    )
    return await _save_demo_trip(connection, schedule, trip_id)


async def _ensure_primary_wallet_credit(
    connection: asyncpg.Connection,
    user_id: int,
) -> None:
    credit_exists = await connection.fetchval(
        """
        SELECT EXISTS (
            SELECT 1
            FROM wallet_transactions
            WHERE user_id = $1
              AND transaction_type = 'wallet_credit'
        )
        """,
        user_id,
    )
    if credit_exists:
        return

    await connection.execute(
        """
        UPDATE users
        SET wallet_balance = wallet_balance + $2
        WHERE id = $1
        """,
        user_id,
        PRIMARY_WALLET_CREDIT,
    )
    await connection.execute(
        """
        INSERT INTO wallet_transactions (
            user_id,
            transaction_type,
            amount
        )
        VALUES ($1, 'wallet_credit', $2)
        """,
        user_id,
        PRIMARY_WALLET_CREDIT,
    )


async def _ensure_primary_booking(
    connection: asyncpg.Connection,
    accounts: SeededDemoAccounts,
    trip_id: int,
) -> None:
    booking_id = await connection.fetchval(
        """
        SELECT id
        FROM bookings
        WHERE trip_id = $1
          AND seat_number = 1
          AND status = 'confirmed'
        """,
        trip_id,
    )
    if booking_id is not None:
        return

    booking = await insert_confirmed_booking(
        connection=connection,
        passenger_profile_id=accounts.passenger_profile_id,
        trip_id=trip_id,
        seat_number=1,
        paid_price=PRIMARY_TICKET_PRICE,
    )
    if booking is None:
        return

    remaining_balance = await debit_wallet(
        connection,
        accounts.operator_user_id,
        PRIMARY_TICKET_PRICE,
    )
    if remaining_balance is None:
        raise RuntimeError("Seed user has insufficient wallet balance")

    await insert_booking_payment(
        connection,
        accounts.operator_user_id,
        booking["id"],
        PRIMARY_TICKET_PRICE,
    )


async def seed_development_data(booking_count: int = 100_000) -> None:
    connection = await asyncpg.connect(dsn=settings.database_url)

    try:
        async with connection.transaction():
            hashed_password = hash_password(DEV_PASSWORD)
            accounts = await _seed_primary_demo_accounts(
                connection,
                hashed_password,
            )
            trip_id = await _seed_primary_demo_trip(
                connection,
                accounts.driver_profile_id,
            )
            await _ensure_primary_wallet_credit(
                connection,
                accounts.operator_user_id,
            )
            await _ensure_primary_booking(connection, accounts, trip_id)
            generated_booking_count = await seed_bulk_bookings(
                connection=connection,
                hashed_password=hashed_password,
                booking_count=booking_count,
            )
            available_trip_count = await seed_available_demo_trips(connection)

        print("Development data seeded.")
        print(f"User mobile: {OPERATOR_MOBILE}")
        print(f"Development password: {DEV_PASSWORD}")
        print(f"Bulk confirmed bookings available: {generated_booking_count}")
        print(f"Available demo trips: {available_trip_count}")
    finally:
        await connection.close()
