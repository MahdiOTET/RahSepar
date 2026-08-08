import asyncpg
from datetime import datetime
from decimal import Decimal


async def get_user_by_mobile(pool: asyncpg.Pool, mobile: str) -> asyncpg.Record | None:
    return await pool.fetchrow(
        """
            SELECT
                id,
                mobile,
                password_hash,
                is_active
            FROM users
            WHERE mobile = $1
        """,
        mobile,
    )


async def get_user_with_profiles(
    pool: asyncpg.Pool, user_id: int
) -> asyncpg.Record | None:
    return await pool.fetchrow(
        """
            SELECT 
                u.id,
                u.mobile,
                u.is_active,
                COALESCE(
                    array_agg(
                        p.profile_type
                        ORDER BY p.profile_type)
                    FILTER (WHERE p.id IS NOT NULL),
                    ARRAY[]::VARCHAR[]
                ) AS profiles
            FROM users AS u
            LEFT JOIN profiles AS p
                on p.user_id = u.id
            WHERE u.id = $1
            GROUP BY 
                u.id,
                u.mobile,
                u.is_active
            """,
        user_id,
    )


async def get_available_tickets(
    pool: asyncpg.Pool,
    origin: str | None,
    destination: str | None,
    sort: str,
    limit: int,
    offset: int,
) -> list[asyncpg.Record]:
    return await pool.fetch(
        """
            SELECT
                t.id AS trip_id,
                r.origin,
                r.destination,
                t.departure_time,
                t.arrival_time,
                t.price,
                b.model AS bus_model,
                b.capacity,
                (
                    b.capacity - count(booking.id)
                )::INTEGER AS available_seats
            FROM trips AS t
            JOIN buses AS b
                ON t.bus_id = b.id 
            JOIN routes AS r
                ON b.route_id = r.id
            LEFT JOIN bookings AS booking
                ON t.id = booking.trip_id
                AND booking.status = 'confirmed'
            WHERE t.status = 'scheduled'
                AND t.departure_time > NOW()
                AND (
                        $1::VARCHAR IS NULL
                        OR lower(r.origin) = lower($1)
                    )
                AND (
                        $2::VARCHAR IS NULL
                        OR lower(r.destination) = lower($2)
                    )
                GROUP BY
                    t.id,
                    r.origin,
                    r.destination,
                    t.departure_time,
                    t.arrival_time,
                    t.price,
                    b.model,
                    b.capacity
                HAVING count(booking.id) < b.capacity
                ORDER BY
                    CASE
                        WHEN $3::TEXT = 'price_asc'
                        THEN t.price
                    END ASC,
                    CASE
                        WHEN $3::TEXT = 'price_desc'
                        THEN t.price
                    END DESC,
                    t.departure_time ASC,
                    t.id ASC
                LIMIT $4
                OFFSET $5                 
        """,
        origin,
        destination,
        sort,
        limit,
        offset,
    )


async def get_booking_context(
    connection: asyncpg.Connection, user_id: int, trip_id: int
) -> tuple[asyncpg.Record | None, int | None, asyncpg.Record | None]:
    user = await connection.fetchrow(
        """
            SELECT id, wallet_balance
            FROM users
            WHERE id = $1
            AND is_active = TRUE
            FOR UPDATE
        """,
        user_id,
    )

    if user is None:
        return None, None, None

    passenger_profile_id = await connection.fetchval(
        """
            SELECT id
            FROM profiles
            WHERE user_id = $1
            AND profile_type = 'passenger'
        """,
        user_id,
    )

    trip = await connection.fetchrow(
        """
            SELECT
                t.id,
                t.price,
                t.status,
                t.departure_time,
                b.capacity,
                (
                    SELECT count(*)
                    FROM bookings AS existing_booking
                    WHERE existing_booking.trip_id = t.id
                    AND existing_booking.status = 'confirmed'
                ) AS confirmed_bookings
            FROM trips AS t
            JOIN buses AS b
                ON b.id = t.bus_id
            WHERE t.id = $1
            FOR SHARE OF t, b
        """,
        trip_id,
    )

    return user, passenger_profile_id, trip


async def count_passenger_bookings_today(
    connection: asyncpg.Connection,
    passenger_profile_id: int,
) -> int:
    return await connection.fetchval(
        """
            SELECT count(*)
            FROM bookings
            WHERE passenger_profile_id = $1
            AND booked_at >= (
                                date_trunc('day',
                                            now() AT TIME ZONE 'Asia/Tehran'
                                            ) AT TIME ZONE 'Asia/Tehran'
                            )
            AND booked_at < (
                                (
                                    date_trunc(
                                                'day',
                                                now() AT TIME ZONE 'Asia/Tehran'
                                                ) + INTERVAL '1 day'
                                ) AT TIME ZONE 'Asia/Tehran'
                            ) 
        """,
        passenger_profile_id,
    )


async def insert_confirmed_booking(
    connection: asyncpg.Connection,
    passenger_profile_id: int,
    trip_id: int,
    seat_number: int,
    paid_price: Decimal,
) -> asyncpg.Record | None:
    return await connection.fetchrow(
        """
            INSERT INTO bookings(
                passenger_profile_id,
                trip_id,
                seat_number,
                paid_price
                )
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (trip_id, seat_number)
                WHERE status = 'confirmed'
            DO NOTHING
            RETURNING
                id,
                trip_id,
                seat_number,
                paid_price,
                status,
                booked_at
        """,
        passenger_profile_id,
        trip_id,
        seat_number,
        paid_price,
    )


async def debit_wallet(
    connection: asyncpg.Connection,
    user_id: int,
    amount: Decimal,
) -> Decimal | None:
    return await connection.fetchval(
        """
            UPDATE users
            SET wallet_balance = wallet_balance - $2
            where id = $1
                AND wallet_balance >= $2
            RETURNING wallet_balance
        """,
        user_id,
        amount,
    )


async def insert_booking_payment(
    connection: asyncpg.Connection, user_id: int, booking_id: int, amount: Decimal
) -> None:
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
        amount,
    )


async def get_booking_for_cancellation(
    connection: asyncpg.Connection,
    booking_id: int,
    user_id: int,
) -> asyncpg.Record | None:
    return await connection.fetchrow(
        """
            SELECT
                b.id,
                b.paid_price,
                b.status,
                b.cancelled_at,
                u.wallet_balance
            FROM bookings AS b
            JOIN profiles AS p
                ON p.id = b.passenger_profile_id
            JOIN users as u
                ON u.id = p.user_id
            WHERE b.id = $1
                AND u.id = $2
                AND u.is_active = TRUE
            FOR UPDATE OF b, u
        """,
        booking_id,
        user_id,
    )


async def mark_booking_cancelled(
    connection: asyncpg.Connection,
    booking_id: int,
) -> asyncpg.Record | None:
    return await connection.fetchrow(
        """
            UPDATE bookings
            SET
                status = 'cancelled',
                cancelled_at = NOW()
            WHERE id = $1
                AND status = 'confirmed'
            RETURNING
                id,
                paid_price,
                status,
                cancelled_at
        """,
        booking_id,
    )


async def credit_wallet(
    connection: asyncpg.Connection,
    user_id: int,
    amount: Decimal,
) -> Decimal | None:
    return await connection.fetchval(
        """
            UPDATE users
            SET wallet_balance = wallet_balance + $2
            WHERE id = $1
            RETURNING wallet_balance
        """,
        user_id,
        amount,
    )


async def insert_booking_refund(
    connection: asyncpg.Connection,
    user_id: int,
    booking_id: int,
    amount: Decimal,
) -> None:
    await connection.execute(
        """
            INSERT INTO wallet_transactions(
                user_id,
                booking_id,
                transaction_type,
                amount
            )
            VALUES($1, $2, 'booking_refund', $3)
        """,
        user_id,
        booking_id,
        amount,
    )


async def upsert_route(
    connection: asyncpg.Connection,
    origin: str,
    destination: str,
) -> int:
    return await connection.fetchval(
        """
            INSERT INTO routes(
                origin,
                destination
            )
            VALUES($1, $2)
            ON CONFLICT (origin, destination)
            DO UPDATE SET
                origin = EXCLUDED.origin
            RETURNING id
        """,
        origin,
        destination,
    )


async def upsert_bus(
    connection: asyncpg.Connection,
    route_id: int,
    plate_number: str,
    model: str | None,
    capacity: int,
) -> asyncpg.Record:
    return await connection.fetchrow(
        """
            WITH imported_bus AS(
                INSERT INTO buses(
                    route_id,
                    plate_number,
                    model,
                    capacity
                )
                VALUES($1, $2, $3, $4)
                ON CONFLICT (plate_number)
                DO UPDATE SET
                    route_id = EXCLUDED.route_id,
                    model = EXCLUDED.model,
                    capacity = EXCLUDED.capacity,
                    is_active = TRUE
                RETURNING
                    id,
                    route_id,
                    plate_number,
                    model,
                    capacity,
                    is_active
            )
            SELECT
                imported_bus.id,
                route.origin,
                route.destination,
                imported_bus.plate_number,
                imported_bus.model,
                imported_bus.capacity,
                imported_bus.is_active
            FROM imported_bus
            JOIN routes AS route
                ON route.id = imported_bus.route_id
        """,
        route_id,
        plate_number,
        model,
        capacity,
    )


async def get_trip_creation_context(
    connection: asyncpg.Connection,
    bus_id: int,
    driver_profile_id: int,
) -> tuple[asyncpg.Record | None, asyncpg.Record | None]:
    bus = await connection.fetchrow(
        """
            SELECT
                b.id,
                b.plate_number,
                b.model,
                r.origin,
                r.destination
            FROM buses AS b
            JOIN routes AS r
                ON r.id = b.route_id
            WHERE b.id = $1
              AND b.is_active = TRUE
            FOR UPDATE OF b
        """,
        bus_id,
    )

    driver = await connection.fetchrow(
        """
            SELECT
                p.id,
                p.display_name
            FROM profiles AS p
            JOIN users AS u
                ON u.id = p.user_id
            WHERE p.id = $1
              AND p.profile_type = 'driver'
              AND u.is_active = TRUE
            FOR UPDATE OF p
        """,
        driver_profile_id,
    )

    return bus, driver


async def get_trip_schedule_conflicts(
    connection: asyncpg.Connection,
    bus_id: int,
    driver_profile_id: int,
    departure_time: datetime,
    arrival_time: datetime,
) -> asyncpg.Record:
    return await connection.fetchrow(
        """
            SELECT
                EXISTS (
                    SELECT 1
                    FROM trips
                    WHERE bus_id = $1
                      AND status = 'scheduled'
                      AND departure_time < $4
                      AND arrival_time > $3
                ) AS bus_has_conflict,
                EXISTS (
                    SELECT 1
                    FROM trips
                    WHERE driver_profile_id = $2
                      AND status = 'scheduled'
                      AND departure_time < $4
                      AND arrival_time > $3
                ) AS driver_has_conflict
        """,
        bus_id,
        driver_profile_id,
        departure_time,
        arrival_time,
    )


async def insert_trip(
    connection: asyncpg.Connection,
    bus_id: int,
    driver_profile_id: int,
    departure_time: datetime,
    arrival_time: datetime,
    price: Decimal,
) -> asyncpg.Record:
    return await connection.fetchrow(
        """
            WITH created_trip AS (
                INSERT INTO trips (
                    bus_id,
                    driver_profile_id,
                    departure_time,
                    arrival_time,
                    price
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING
                    id,
                    bus_id,
                    driver_profile_id,
                    departure_time,
                    arrival_time,
                    price,
                    status
            )
            SELECT
                created_trip.id,
                created_trip.bus_id,
                created_trip.driver_profile_id,
                route.origin,
                route.destination,
                bus.plate_number,
                bus.model AS bus_model,
                driver.display_name AS driver_name,
                created_trip.departure_time,
                created_trip.arrival_time,
                created_trip.price,
                created_trip.status
            FROM created_trip
            JOIN buses AS bus
                ON bus.id = created_trip.bus_id
            JOIN routes AS route
                ON route.id = bus.route_id
            JOIN profiles AS driver
                ON driver.id = created_trip.driver_profile_id
        """,
        bus_id,
        driver_profile_id,
        departure_time,
        arrival_time,
        price,
    )
