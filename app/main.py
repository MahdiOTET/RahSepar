from fastapi import FastAPI
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.db import create_pool


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    pool = await create_pool()
    application.state.database_pool = pool

    try:
        yield
    finally:
        await pool.close()


def create_app() -> FastAPI:
    application = FastAPI(title="Intercity Bus Ticket Booking", version="1.0.0")

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
