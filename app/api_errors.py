from dataclasses import dataclass

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.errors import (
    BookingConflictError,
    BookingForbiddenError,
    BookingNotFoundError,
    BookingValidationError,
    BusImportValidationError,
    InvalidAccessTokenError,
    InvalidCredentialError,
    ReportValidationError,
    ServiceError,
    TripConflictError,
    TripNotFoundError,
    TripValidationError,
)


@dataclass(frozen=True)
class ServiceErrorResponse:
    status_code: int
    headers: dict[str, str] | None = None


AUTHENTICATION_HEADERS = {"WWW-Authenticate": "Bearer"}

SERVICE_ERROR_RESPONSES: dict[type[ServiceError], ServiceErrorResponse] = {
    InvalidCredentialError: ServiceErrorResponse(
        status.HTTP_401_UNAUTHORIZED,
        AUTHENTICATION_HEADERS,
    ),
    InvalidAccessTokenError: ServiceErrorResponse(
        status.HTTP_401_UNAUTHORIZED,
        AUTHENTICATION_HEADERS,
    ),
    BookingForbiddenError: ServiceErrorResponse(status.HTTP_403_FORBIDDEN),
    BookingNotFoundError: ServiceErrorResponse(status.HTTP_404_NOT_FOUND),
    BookingValidationError: ServiceErrorResponse(status.HTTP_422_UNPROCESSABLE_CONTENT),
    BookingConflictError: ServiceErrorResponse(status.HTTP_409_CONFLICT),
    BusImportValidationError: ServiceErrorResponse(
        status.HTTP_422_UNPROCESSABLE_CONTENT
    ),
    TripNotFoundError: ServiceErrorResponse(status.HTTP_404_NOT_FOUND),
    TripValidationError: ServiceErrorResponse(status.HTTP_422_UNPROCESSABLE_CONTENT),
    TripConflictError: ServiceErrorResponse(status.HTTP_409_CONFLICT),
    ReportValidationError: ServiceErrorResponse(status.HTTP_422_UNPROCESSABLE_CONTENT),
}


async def service_error_response(
    _request: Request,
    error: ServiceError,
) -> JSONResponse:
    response = SERVICE_ERROR_RESPONSES[type(error)]
    return JSONResponse(
        status_code=response.status_code,
        content={"detail": str(error)},
        headers=response.headers,
    )


def register_service_error_handler(application: FastAPI) -> None:
    application.add_exception_handler(ServiceError, service_error_response)
