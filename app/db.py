import asyncpg

from app.config import settings
from fastapi import Request


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=10)


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.database_pool
