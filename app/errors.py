class ServiceError(Exception):
    default_detail = "Request could not be completed"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.default_detail)


class InvalidCredentialError(ServiceError):
    default_detail = "Invalid Mobile or Password"


class InvalidAccessTokenError(ServiceError):
    default_detail = "Invalid or expired access token"


class BookingForbiddenError(ServiceError):
    pass


class BookingNotFoundError(ServiceError):
    pass


class BookingValidationError(ServiceError):
    pass


class BookingConflictError(ServiceError):
    pass


class BusImportValidationError(ServiceError):
    pass


class TripNotFoundError(ServiceError):
    pass


class TripValidationError(ServiceError):
    pass


class TripConflictError(ServiceError):
    pass


class ReportValidationError(ServiceError):
    pass
