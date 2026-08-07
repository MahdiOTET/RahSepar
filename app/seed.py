from datetime import UTC, datetime, timedelta
from decimal import Decimal

import asyncpg

from app.config import settings
from app.security import hash_password

DEV_PASSWORD = "DevPass123!"


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


async def seed_development_data() -> None:
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
                "Development Passenger",
                "passenger",
            )

            await upsert_profile(
                connection,
                user_id,
                "Development Operator",
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
                "Development Driver",
                "driver",
            )

            route_id = await connection.fetchval("""
                INSERT INTO routes (origin, destination)
                VALUES ('Tehran', 'Shiraz')
                ON CONFLICT (origin, destination)
                DO UPDATE SET origin = EXCLUDED.origin
                RETURNING id
                """)

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

        print("Development data seeded.")
        print("User mobile: 09123456789")
        print(f"Development password: {DEV_PASSWORD}")

    finally:
        await connection.close()
