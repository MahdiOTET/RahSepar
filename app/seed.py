from datetime import UTC, datetime, timedelta
from decimal import Decimal

import asyncpg

from app.config import settings
from app.security import hash_password

DEV_PASSWORD = "DevPass123!"
BULK_BOOKING_PRICE = Decimal("1000000.00")
BULK_INITIAL_CREDIT = Decimal("50000000.00")
BULK_BUS_COUNT = 20
BULK_DRIVER_COUNT = 20
BULK_BUS_CAPACITY = 100
BULK_DAILY_BOOKING_LIMIT = 20

BULK_ROUTES = (
    ("تهران", "مشهد"),
    ("مشهد", "تهران"),
    ("شیراز", "تهران"),
    ("تهران", "اصفهان"),
    ("اصفهان", "تهران"),
)

DEMO_ROUTES = (
    ("تهران", "شیراز", "Volvo B9R", Decimal("950000.00"), 10),
    ("تهران", "مشهد", "Scania Maral", Decimal("1250000.00"), 12),
    ("مشهد", "تهران", "Volvo B11R", Decimal("1200000.00"), 12),
    ("شیراز", "تهران", "Scania Classic", Decimal("900000.00"), 10),
    ("تهران", "اصفهان", "MAN Lion's Coach", Decimal("720000.00"), 6),
    ("اصفهان", "تهران", "Volvo B9R", Decimal("680000.00"), 6),
)


async def upsert_user(
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


async def upsert_profile(
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


async def seed_bulk_bookings(
    connection: asyncpg.Connection,
    hashed_password: str,
    booking_count: int,
) -> int:
    if booking_count < 0:
        raise ValueError("booking_count must not be negative")

    if booking_count > 1_000_000:
        raise ValueError("booking_count must not exceed 1,000,000")

    if booking_count == 0:
        return 0

    passenger_count = (
        booking_count + BULK_DAILY_BOOKING_LIMIT - 1
    ) // BULK_DAILY_BOOKING_LIMIT
    trip_count = (booking_count + BULK_BUS_CAPACITY - 1) // BULK_BUS_CAPACITY

    driver_profile_ids: list[int] = []

    for number in range(1, BULK_DRIVER_COUNT + 1):
        driver_user_id = await upsert_user(
            connection=connection,
            mobile=f"097{number:08d}",
            hashed_password=hashed_password,
        )
        driver_profile_ids.append(
            await upsert_profile(
                connection=connection,
                user_id=driver_user_id,
                display_name=f"راننده آزمایشی {number}",
                profile_type="driver",
            )
        )

    route_ids: list[int] = []

    for origin, destination in BULK_ROUTES:
        route_ids.append(
            await connection.fetchval(
                """
                    INSERT INTO routes (origin, destination)
                    VALUES ($1, $2)
                    ON CONFLICT (origin, destination)
                    DO UPDATE SET origin = EXCLUDED.origin
                    RETURNING id
                """,
                origin,
                destination,
            )
        )

    bus_ids: list[int] = []

    for number in range(1, BULK_BUS_COUNT + 1):
        bus_ids.append(
            await connection.fetchval(
                """
                    INSERT INTO buses (
                        route_id,
                        plate_number,
                        model,
                        capacity
                    )
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (plate_number)
                    DO UPDATE SET
                        route_id = EXCLUDED.route_id,
                        model = EXCLUDED.model,
                        capacity = EXCLUDED.capacity,
                        is_active = TRUE
                    RETURNING id
                """,
                route_ids[(number - 1) % len(route_ids)],
                f"LOAD-{number:03d}",
                "اتوبوس داده آزمایشی",
                BULK_BUS_CAPACITY,
            )
        )

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

    passenger_rows = await connection.fetch(
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

    trip_rows = await connection.fetch(
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


async def seed_available_demo_trips(connection: asyncpg.Connection) -> int:
    driver_rows = await connection.fetch(
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

    if len(driver_rows) < len(DEMO_ROUTES):
        raise RuntimeError("Not enough active drivers to seed available trips")

    seeded_trip_count = 0
    demo_anchor = datetime.now(UTC).replace(
        hour=5,
        minute=30,
        second=0,
        microsecond=0,
    )

    for route_index, (
        origin,
        destination,
        model,
        base_price,
        duration_hours,
    ) in enumerate(DEMO_ROUTES):
        route_id = await connection.fetchval(
            """
                INSERT INTO routes (origin, destination)
                VALUES ($1, $2)
                ON CONFLICT (origin, destination)
                DO UPDATE SET origin = EXCLUDED.origin
                RETURNING id
            """,
            origin,
            destination,
        )
        bus_id = await connection.fetchval(
            """
                INSERT INTO buses (
                    route_id,
                    plate_number,
                    model,
                    capacity
                )
                VALUES ($1, $2, $3, 40)
                ON CONFLICT (plate_number)
                DO UPDATE SET
                    route_id = EXCLUDED.route_id,
                    model = EXCLUDED.model,
                    capacity = EXCLUDED.capacity,
                    is_active = TRUE
                RETURNING id
            """,
            route_id,
            f"RSP-{route_index + 1:03d}",
            model,
        )
        reusable_trip_ids = [
            row["id"]
            for row in await connection.fetch(
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
        ]

        for slot in range(3):
            departure_time = demo_anchor + timedelta(
                days=2 + slot * 2,
                minutes=route_index * 20,
            )
            arrival_time = departure_time + timedelta(hours=duration_hours)
            price = base_price + Decimal(slot * 125_000)
            driver_profile_id = driver_rows[route_index]["id"]

            if slot < len(reusable_trip_ids):
                await connection.execute(
                    """
                        UPDATE trips
                        SET
                            driver_profile_id = $2,
                            departure_time = $3,
                            arrival_time = $4,
                            price = $5,
                            status = 'scheduled'
                        WHERE id = $1
                    """,
                    reusable_trip_ids[slot],
                    driver_profile_id,
                    departure_time,
                    arrival_time,
                    price,
                )
            else:
                await connection.execute(
                    """
                        INSERT INTO trips (
                            bus_id,
                            driver_profile_id,
                            departure_time,
                            arrival_time,
                            price
                        )
                        VALUES ($1, $2, $3, $4, $5)
                    """,
                    bus_id,
                    driver_profile_id,
                    departure_time,
                    arrival_time,
                    price,
                )

            seeded_trip_count += 1

    return seeded_trip_count


async def seed_development_data(booking_count: int = 100_000) -> None:
    connection = await asyncpg.connect(dsn=settings.database_url)

    try:
        async with connection.transaction():
            hashed_password = hash_password(DEV_PASSWORD)

            # This user can act as both passenger and operator.
            user_id = await upsert_user(
                connection,
                "09123456789",
                hashed_password,
            )

            passenger_profile_id = await upsert_profile(
                connection,
                user_id,
                "مسافر آزمایشی",
                "passenger",
            )

            await upsert_profile(
                connection,
                user_id,
                "مدیر آزمایشی",
                "operator",
            )

            # Separate driver account.
            driver_user_id = await upsert_user(
                connection,
                "09120000002",
                hashed_password,
            )

            driver_profile_id = await upsert_profile(
                connection,
                driver_user_id,
                "راننده آزمایشی اصلی",
                "driver",
            )

            route_id = await connection.fetchval(
                """
                INSERT INTO routes (origin, destination)
                VALUES ('تهران', 'شیراز')
                ON CONFLICT (origin, destination)
                DO UPDATE SET origin = EXCLUDED.origin
                RETURNING id
                """
            )

            bus_id = await connection.fetchval(
                """
                INSERT INTO buses (
                    route_id,
                    plate_number,
                    model,
                    capacity
                )
                VALUES ($1, '11A111-11', 'Volvo B9R', 40)
                ON CONFLICT (plate_number)
                DO UPDATE SET
                    route_id = EXCLUDED.route_id,
                    model = EXCLUDED.model,
                    capacity = EXCLUDED.capacity,
                    is_active = TRUE
                RETURNING id
                """,
                route_id,
            )

            departure_time = datetime.now(UTC) + timedelta(days=1)
            arrival_time = departure_time + timedelta(hours=10)
            ticket_price = Decimal("1000000.00")

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

            if trip_id is None:
                trip_id = await connection.fetchval(
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
                    bus_id,
                    driver_profile_id,
                    departure_time,
                    arrival_time,
                    ticket_price,
                )
            else:
                await connection.execute(
                    """
                    UPDATE trips
                    SET driver_profile_id = $2,
                        departure_time = $3,
                        arrival_time = $4,
                        price = $5,
                        status = 'scheduled'
                    WHERE id = $1
                    """,
                    trip_id,
                    driver_profile_id,
                    departure_time,
                    arrival_time,
                    ticket_price,
                )

            initial_credit = Decimal("10000000.00")

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

            if not credit_exists:
                await connection.execute(
                    """
                    UPDATE users
                    SET wallet_balance = wallet_balance + $2
                    WHERE id = $1
                    """,
                    user_id,
                    initial_credit,
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
                    initial_credit,
                )

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

            if booking_id is None:
                booking_id = await connection.fetchval(
                    """
                    INSERT INTO bookings (
                        passenger_profile_id,
                        trip_id,
                        seat_number,
                        paid_price
                    )
                    VALUES ($1, $2, 1, $3)
                    RETURNING id
                    """,
                    passenger_profile_id,
                    trip_id,
                    ticket_price,
                )

                updated_user_id = await connection.fetchval(
                    """
                    UPDATE users
                    SET wallet_balance = wallet_balance - $2
                    WHERE id = $1
                      AND wallet_balance >= $2
                    RETURNING id
                    """,
                    user_id,
                    ticket_price,
                )

                if updated_user_id is None:
                    raise RuntimeError("Seed user has insufficient wallet balance")

                await connection.execute(
                    """
                    INSERT INTO wallet_transactions (
                        user_id,
                        booking_id,
                        transaction_type,
                        amount
                    )
                    VALUES ($1, $2, 'booking_payment', $3)
                    """,
                    user_id,
                    booking_id,
                    ticket_price,
                )

            generated_booking_count = await seed_bulk_bookings(
                connection=connection,
                hashed_password=hashed_password,
                booking_count=booking_count,
            )
            available_trip_count = await seed_available_demo_trips(connection)

        print("Development data seeded.")
        print("User mobile: 09123456789")
        print(f"Development password: {DEV_PASSWORD}")
        print(f"Bulk confirmed bookings available: {generated_booking_count}")
        print(f"Available demo trips: {available_trip_count}")

    finally:
        await connection.close()
