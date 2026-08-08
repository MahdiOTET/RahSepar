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
