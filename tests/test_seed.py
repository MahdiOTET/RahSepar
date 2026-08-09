import asyncpg

from app.seed import seed_available_demo_trips, seed_bulk_bookings


async def test_bulk_seeder_is_valid_and_repeatable(
    test_pool: asyncpg.Pool,
    seeded_data: dict,
    test_password_hash: str,
) -> None:
    async with test_pool.acquire() as connection:
        async with connection.transaction():
            first_count = await seed_bulk_bookings(
                connection=connection,
                hashed_password=test_password_hash,
                booking_count=250,
            )

        async with connection.transaction():
            second_count = await seed_bulk_bookings(
                connection=connection,
                hashed_password=test_password_hash,
                booking_count=250,
            )

        async with connection.transaction():
            first_demo_count = await seed_available_demo_trips(connection)
            second_demo_count = await seed_available_demo_trips(connection)

        invariants = await connection.fetchrow(
            """
                WITH load_profiles AS (
                    SELECT profile.id
                    FROM profiles AS profile
                    JOIN users AS app_user
                        ON app_user.id = profile.user_id
                    WHERE app_user.mobile LIKE '098%'
                      AND profile.profile_type = 'passenger'
                ),
                daily_counts AS (
                    SELECT
                        booking.passenger_profile_id,
                        (
                            booking.booked_at AT TIME ZONE 'Asia/Tehran'
                        )::DATE AS local_date,
                        count(*) AS booking_count
                    FROM bookings AS booking
                    JOIN load_profiles AS profile
                        ON profile.id = booking.passenger_profile_id
                    GROUP BY booking.passenger_profile_id, local_date
                )
                SELECT
                    (SELECT max(booking_count) FROM daily_counts) AS max_daily,
                    (
                        SELECT count(*)
                        FROM wallet_transactions AS transaction
                        JOIN bookings AS booking
                            ON booking.id = transaction.booking_id
                        JOIN load_profiles AS profile
                            ON profile.id = booking.passenger_profile_id
                        WHERE transaction.transaction_type = 'booking_payment'
                    ) AS payments,
                    (
                        SELECT count(*)
                        FROM users AS app_user
                        WHERE app_user.mobile LIKE '098%'
                          AND app_user.wallet_balance < 0
                    ) AS negative_wallets
            """
        )
        demo_catalog = await connection.fetchrow(
            """
                SELECT
                    count(DISTINCT route.id) AS route_count,
                    count(DISTINCT trip.id) AS trip_count,
                    count(DISTINCT trip.price) AS price_count
                FROM buses AS bus
                JOIN routes AS route
                    ON route.id = bus.route_id
                JOIN trips AS trip
                    ON trip.bus_id = bus.id
                WHERE bus.plate_number LIKE 'RSP-%'
                  AND trip.status = 'scheduled'
                  AND trip.departure_time > NOW()
            """
        )

    assert first_count == 250
    assert second_count == 250
    assert first_demo_count == 18
    assert second_demo_count == 18
    assert invariants["max_daily"] <= 20
    assert invariants["payments"] == 250
    assert invariants["negative_wallets"] == 0
    assert demo_catalog["route_count"] == 6
    assert demo_catalog["trip_count"] == 18
    assert demo_catalog["price_count"] > 3
