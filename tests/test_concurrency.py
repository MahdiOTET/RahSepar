import asyncio
from time import perf_counter

import asyncpg
import httpx


async def test_same_seat_concurrency_is_safe_and_under_two_seconds(
    api_client: httpx.AsyncClient,
    test_pool: asyncpg.Pool,
    seeded_data: dict,
    login_headers,
) -> None:
    first_headers = await login_headers("09100000001")
    second_headers = await login_headers("09100000002")
    payload = {"trip_id": seeded_data["trip_id"], "seat_number": 12}

    started = perf_counter()
    responses = await asyncio.gather(
        api_client.post("/api/v1/bookings", headers=first_headers, json=payload),
        api_client.post("/api/v1/bookings", headers=second_headers, json=payload),
    )
    elapsed = perf_counter() - started

    assert sorted(response.status_code for response in responses) == [201, 409]
    assert elapsed < 2.0

    booking_count = await test_pool.fetchval(
        """
            SELECT count(*)
            FROM bookings
            WHERE trip_id = $1
              AND seat_number = 12
              AND status = 'confirmed'
        """,
        seeded_data["trip_id"],
    )
    payment_count = await test_pool.fetchval(
        """
            SELECT count(*)
            FROM wallet_transactions AS transaction
            JOIN bookings AS booking
                ON booking.id = transaction.booking_id
            WHERE booking.trip_id = $1
              AND booking.seat_number = 12
              AND transaction.transaction_type = 'booking_payment'
        """,
        seeded_data["trip_id"],
    )

    assert booking_count == 1
    assert payment_count == 1
