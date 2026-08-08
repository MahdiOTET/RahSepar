from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import asyncpg
import httpx


async def test_login_current_user_and_invalid_credentials(
    api_client: httpx.AsyncClient,
    login_headers,
) -> None:
    headers = await login_headers("09100000001")
    current_user = await api_client.get("/api/v1/users/me", headers=headers)

    assert current_user.status_code == 200
    assert current_user.json()["mobile"] == "09100000001"
    assert current_user.json()["profiles"] == ["operator", "passenger"]

    invalid_login = await api_client.post(
        "/api/v1/auth/login",
        json={"mobile": "09100000001", "password": "WrongPass123!"},
    )
    assert invalid_login.status_code == 401

    missing_token = await api_client.get("/api/v1/users/me")
    assert missing_token.status_code == 401


async def test_ticket_booking_and_daily_limit(
    api_client: httpx.AsyncClient,
    test_pool: asyncpg.Pool,
    seeded_data: dict,
    login_headers,
) -> None:
    headers = await login_headers("09100000001")

    tickets_before = await api_client.get("/api/v1/tickets")
    assert tickets_before.status_code == 200
    assert tickets_before.json()[0]["available_seats"] == 40

    booking = await api_client.post(
        "/api/v1/bookings",
        headers=headers,
        json={"trip_id": seeded_data["trip_id"], "seat_number": 1},
    )
    assert booking.status_code == 201
    assert booking.json()["remaining_wallet_balance"] == "9000000.00"

    duplicate = await api_client.post(
        "/api/v1/bookings",
        headers=headers,
        json={"trip_id": seeded_data["trip_id"], "seat_number": 1},
    )
    assert duplicate.status_code == 409

    async with test_pool.acquire() as connection:
        await connection.execute(
            "DELETE FROM wallet_transactions WHERE transaction_type = 'booking_payment'"
        )
        await connection.execute("DELETE FROM bookings")
        await connection.execute(
            """
                INSERT INTO bookings (
                    passenger_profile_id,
                    trip_id,
                    seat_number,
                    paid_price
                )
                SELECT $1, $2, seat_number, 1000000.00
                FROM generate_series(1, 20) AS seat_number
            """,
            seeded_data["operator_passenger_profile_id"],
            seeded_data["trip_id"],
        )

    daily_limit = await api_client.post(
        "/api/v1/bookings",
        headers=headers,
        json={"trip_id": seeded_data["trip_id"], "seat_number": 21},
    )
    assert daily_limit.status_code == 409
    assert daily_limit.json()["detail"] == "Daily booking limit has been reached"


async def test_cancellation_is_owned_and_idempotent(
    api_client: httpx.AsyncClient,
    test_pool: asyncpg.Pool,
    seeded_data: dict,
    login_headers,
) -> None:
    owner_headers = await login_headers("09100000001")
    other_headers = await login_headers("09100000002")

    booking = await api_client.post(
        "/api/v1/bookings",
        headers=owner_headers,
        json={"trip_id": seeded_data["trip_id"], "seat_number": 5},
    )
    booking_id = booking.json()["id"]

    not_owner = await api_client.delete(
        f"/api/v1/bookings/{booking_id}",
        headers=other_headers,
    )
    assert not_owner.status_code == 404

    first = await api_client.delete(
        f"/api/v1/bookings/{booking_id}",
        headers=owner_headers,
    )
    second = await api_client.delete(
        f"/api/v1/bookings/{booking_id}",
        headers=owner_headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["remaining_wallet_balance"] == "10000000.00"
    assert second.json()["remaining_wallet_balance"] == "10000000.00"

    refund_count = await test_pool.fetchval(
        """
            SELECT count(*)
            FROM wallet_transactions
            WHERE booking_id = $1
              AND transaction_type = 'booking_refund'
        """,
        booking_id,
    )
    assert refund_count == 1


async def test_operator_bus_import_and_trip_creation(
    api_client: httpx.AsyncClient,
    seeded_data: dict,
    login_headers,
) -> None:
    operator_headers = await login_headers("09100000001")
    driver_headers = await login_headers("09100000003")
    bus_payload = {
        "buses": [
            {
                "origin": "Tehran",
                "destination": "Mashhad",
                "plate_number": "TEST-002",
                "model": "Second Test Coach",
                "capacity": 44,
            }
        ]
    }

    forbidden_import = await api_client.post(
        "/api/v1/buses",
        headers=driver_headers,
        json=bus_payload,
    )
    assert forbidden_import.status_code == 403

    imported = await api_client.post(
        "/api/v1/buses",
        headers=operator_headers,
        json=bus_payload,
    )
    assert imported.status_code == 201
    assert imported.json()["imported_count"] == 1
    bus_id = imported.json()["buses"][0]["id"]

    departure = datetime.now(UTC) + timedelta(days=10)
    arrival = departure + timedelta(hours=12)
    trip_payload = {
        "bus_id": bus_id,
        "driver_profile_id": seeded_data["driver_profile_id"],
        "departure_time": departure.isoformat(),
        "arrival_time": arrival.isoformat(),
        "price": "1500000.00",
    }

    created = await api_client.post(
        "/api/v1/trips",
        headers=operator_headers,
        json=trip_payload,
    )
    assert created.status_code == 201
    assert created.json()["plate_number"] == "TEST-002"

    overlapping = await api_client.post(
        "/api/v1/trips",
        headers=operator_headers,
        json=trip_payload,
    )
    assert overlapping.status_code == 409

    forbidden_trip = await api_client.post(
        "/api/v1/trips",
        headers=driver_headers,
        json=trip_payload,
    )
    assert forbidden_trip.status_code == 403

    naive_payload = dict(trip_payload)
    naive_payload["departure_time"] = departure.replace(tzinfo=None).isoformat()
    naive_payload["arrival_time"] = arrival.replace(tzinfo=None).isoformat()
    naive = await api_client.post(
        "/api/v1/trips",
        headers=operator_headers,
        json=naive_payload,
    )
    assert naive.status_code == 422


async def test_operator_reports(
    api_client: httpx.AsyncClient,
    test_pool: asyncpg.Pool,
    seeded_data: dict,
    login_headers,
) -> None:
    operator_headers = await login_headers("09100000001")
    driver_headers = await login_headers("09100000003")

    booking = await api_client.post(
        "/api/v1/bookings",
        headers=operator_headers,
        json={"trip_id": seeded_data["trip_id"], "seat_number": 7},
    )
    assert booking.status_code == 201

    known_booking_time = datetime(2026, 1, 15, 12, 30, tzinfo=UTC)
    await test_pool.execute(
        "UPDATE bookings SET booked_at = $2 WHERE id = $1",
        booking.json()["id"],
        known_booking_time,
    )
    await test_pool.execute(
        """
            UPDATE trips
            SET
                departure_time = TIMESTAMPTZ '2030-01-20 08:00:00+00',
                arrival_time = TIMESTAMPTZ '2030-01-20 16:00:00+00'
            WHERE id = $1
        """,
        seeded_data["trip_id"],
    )

    hourly = await api_client.get(
        "/api/v1/reports/hourly-bookings",
        headers=operator_headers,
        params={"report_date": "2026-01-15"},
    )
    assert hourly.status_code == 200
    assert hourly.json()["total_confirmed_bookings"] == 1
    assert hourly.json()["hours"][16]["confirmed_bookings"] == 1

    monthly = await api_client.get(
        "/api/v1/reports/monthly-buses",
        headers=operator_headers,
        params={"year": 2030, "month": 1},
    )
    assert monthly.status_code == 200
    bus_row = next(
        row
        for row in monthly.json()["buses"]
        if row["bus_id"] == seeded_data["bus_id"]
    )
    assert bus_row["trip_count"] == 1
    assert bus_row["confirmed_bookings"] == 1

    busiest = await api_client.get(
        "/api/v1/reports/busiest-drivers",
        headers=operator_headers,
        params={"date_from": "2030-01-01", "date_to": "2030-01-31"},
    )
    assert busiest.status_code == 200
    assert busiest.json()["drivers"][0]["driver_profile_id"] == seeded_data[
        "driver_profile_id"
    ]

    forbidden = await api_client.get(
        "/api/v1/reports/monthly-buses",
        headers=driver_headers,
        params={"year": 2030, "month": 1},
    )
    assert forbidden.status_code == 403

    invalid_range = await api_client.get(
        "/api/v1/reports/busiest-drivers",
        headers=operator_headers,
        params={"date_from": "2030-02-01", "date_to": "2030-01-01"},
    )
    assert invalid_range.status_code == 422
