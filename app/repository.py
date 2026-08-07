import asyncpg


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
