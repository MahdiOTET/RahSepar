from pathlib import Path
import asyncpg
from app.config import settings

MIGRATIONS_DIRECTORY = Path(__file__).resolve().parent.parent / "migrations"


async def run_migrations() -> None:
    connection = await asyncpg.connect(dsn=settings.database_url)

    try:
        await connection.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)

        rows = await connection.fetch("SELECT VERSION FROM schema_migrations")

        applied_version = {row["version"] for row in rows}

        migration_files = sorted(MIGRATIONS_DIRECTORY.glob("*.sql"))

        for migration_file in migration_files:
            version = migration_file.stem

            if version in applied_version:
                continue

            sql = migration_file.read_text(encoding="utf-8")

            async with connection.transaction():
                await connection.execute(sql)
                await connection.execute(
                    """
                        INSERT INTO schema_migrations (version)
                        VALUES ($1)

                    """,
                    version,
                )
            print(f"Applied Migration : {version}")

        print("Database migrations are up to date")

    finally:
        await connection.close()
