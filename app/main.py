from fastapi import FastAPI


def create_app() -> FastAPI:
    application = FastAPI(title="Intercity Bus Ticket Booking", version="1.0.0")

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
