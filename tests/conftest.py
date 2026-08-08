from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import asyncpg
import httpx
import pytest
import pytest_asyncio

from app.config import settings
from app.db import get_pool
from app.main import app
from app.security import hash_password


MIGRATIONS_DIRECTORY = Path(__file__).resolve().parent.parent / "migrations"
TEST_PASSWORD = "TestPass123!"


@pytest.fixture(scope="session")
def test_password_hash() -> str:
    return hash_password(TEST_PASSWORD)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def test_pool() -> AsyncIterator[asyncpg.Pool]:
    schema_name = f"test_{uuid4().hex}"
    admin_connection = await asyncpg.connect(settings.database_url)

    try:
        await admin_connection.execute(f'CREATE SCHEMA "{schema_name}"')
        await admin_connection.execute(f'SET search_path TO "{schema_name}"')

        async with admin_connection.transaction():
            for migration_file in sorted(MIGRATIONS_DIRECTORY.glob("*.sql")):
                await admin_connection.execute(
                    migration_file.read_text(encoding="utf-8")
                )

        pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=1,
            max_size=20,
            server_settings={
                "search_path": schema_name,
                "timezone": "UTC",
            },
        )

        try:
            yield pool
        finally:
            await pool.close()
    finally:
        await admin_connection.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
        await admin_connection.close()


@pytest_asyncio.fixture(loop_scope="session")
async def seeded_data(
    test_pool: asyncpg.Pool,
    test_password_hash: str,
) -> dict[str, int | datetime]:
    async with test_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                """
                    TRUNCATE TABLE
                        wallet_transactions,
                        bookings,
                        trips,
                        buses,
                        routes,
                        profiles,
                        users
                    RESTART IDENTITY CASCADE
                """
            )

            operator_user_id = await connection.fetchval(
                """
                    INSERT INTO users (
                        mobile,
                        password_hash,
                        wallet_balance
                    )
                    VALUES ('09100000001', $1, 10000000.00)
                    RETURNING id
                """,
                test_password_hash,
            )
            second_user_id = await connection.fetchval(
                """
                    INSERT INTO users (
                        mobile,
                        password_hash,
                        wallet_balance
                    )
                    VALUES ('09100000002', $1, 10000000.00)
                    RETURNING id
                """,
                test_password_hash,
            )
            driver_user_id = await connection.fetchval(
                """
                    INSERT INTO users (mobile, password_hash)
                    VALUES ('09100000003', $1)
                    RETURNING id
                """,
                test_password_hash,
            )

            operator_passenger_profile_id = await connection.fetchval(
                """
                    INSERT INTO profiles (
                        user_id,
                        display_name,
                        profile_type
                    )
                    VALUES ($1, 'Test Operator Passenger', 'passenger')
                    RETURNING id
                """,
                operator_user_id,
            )
            await connection.execute(
                """
                    INSERT INTO profiles (
                        user_id,
                        display_name,
                        profile_type
                    )
                    VALUES ($1, 'Test Operator', 'operator')
                """,
                operator_user_id,
            )
            second_passenger_profile_id = await connection.fetchval(
                """
                    INSERT INTO profiles (
                        user_id,
                        display_name,
                        profile_type
                    )
                    VALUES ($1, 'Second Passenger', 'passenger')
                    RETURNING id
                """,
                second_user_id,
            )
            driver_profile_id = await connection.fetchval(
                """
                    INSERT INTO profiles (
                        user_id,
                        display_name,
                        profile_type
                    )
                    VALUES ($1, 'Test Driver', 'driver')
                    RETURNING id
                """,
                driver_user_id,
            )

            route_id = await connection.fetchval(
                """
                    INSERT INTO routes (origin, destination)
                    VALUES ('Tehran', 'Tabriz')
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
                    VALUES ($1, 'TEST-001', 'Test Coach', 40)
                    RETURNING id
                """,
                route_id,
            )

            departure_time = datetime.now(UTC) + timedelta(days=2)
            arrival_time = departure_time + timedelta(hours=8)
            trip_id = await connection.fetchval(
                """
                    INSERT INTO trips (
                        bus_id,
                        driver_profile_id,
                        departure_time,
                        arrival_time,
                        price
                    )
                    VALUES ($1, $2, $3, $4, 1000000.00)
                    RETURNING id
                """,
                bus_id,
                driver_profile_id,
                departure_time,
                arrival_time,
            )

            await connection.executemany(
                """
                    INSERT INTO wallet_transactions (
                        user_id,
                        transaction_type,
                        amount
                    )
                    VALUES ($1, 'wallet_credit', 10000000.00)
                """,
                [(operator_user_id,), (second_user_id,)],
            )

    return {
        "operator_user_id": operator_user_id,
        "second_user_id": second_user_id,
        "driver_user_id": driver_user_id,
        "operator_passenger_profile_id": operator_passenger_profile_id,
        "second_passenger_profile_id": second_passenger_profile_id,
        "driver_profile_id": driver_profile_id,
        "bus_id": bus_id,
        "trip_id": trip_id,
        "departure_time": departure_time,
        "arrival_time": arrival_time,
    }


@pytest_asyncio.fixture(loop_scope="session")
async def api_client(
    test_pool: asyncpg.Pool,
    seeded_data: dict[str, int | datetime],
) -> AsyncIterator[httpx.AsyncClient]:
    async def override_pool() -> asyncpg.Pool:
        return test_pool

    app.dependency_overrides[get_pool] = override_pool
    transport = httpx.ASGITransport(app=app)

    try:
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def login_headers(
    api_client: httpx.AsyncClient,
) -> Callable[[str], Awaitable[dict[str, str]]]:
    async def login(mobile: str) -> dict[str, str]:
        response = await api_client.post(
            "/api/v1/auth/login",
            json={"mobile": mobile, "password": TEST_PASSWORD},
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return login
