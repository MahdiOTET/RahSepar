from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.api_errors import register_service_error_handler
from app.db import create_pool

PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
FRONTEND_DIRECTORY = PROJECT_DIRECTORY / "frontend" / "dist"


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    pool = await create_pool()
    application.state.database_pool = pool

    try:
        yield
    finally:
        await pool.close()


def add_frontend(application: FastAPI, directory: Path) -> None:
    index_file = directory / "index.html"
    if not index_file.is_file():
        return

    assets_directory = directory / "assets"
    if assets_directory.is_dir():
        application.mount(
            "/assets",
            StaticFiles(directory=assets_directory),
            name="frontend-assets",
        )

    @application.get("/{path:path}", include_in_schema=False)
    async def serve_frontend(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        requested_file = (directory / path).resolve()
        try:
            requested_file.relative_to(directory.resolve())
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from err

        if path and requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(index_file)


def create_app(frontend_directory: Path = FRONTEND_DIRECTORY) -> FastAPI:
    application = FastAPI(
        title="Intercity Bus Ticket Booking",
        version="2.0.0",
        lifespan=lifespan,
    )

    register_service_error_handler(application)
    application.include_router(api_router, prefix="/api/v1")

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    add_frontend(application, frontend_directory)

    return application


app = create_app()
