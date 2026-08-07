import asyncpg

from app.config import settings


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=10)
