from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    mobile: str = Field(
        min_length=10,
        max_length=15,
        pattern=r"^\+?\d+$",
    )

    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class CurrentUserResponse(BaseModel):
    id: int
    mobile: str
    display_name: str
    wallet_balance: Decimal
    profiles: list[str]


class TicketSort(str, Enum):
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    DEPARTURE_ASC = "departure_asc"
    DEPARTURE_DESC = "departure_desc"


class TicketQuery(BaseModel):
    origin: str | None = Field(default=None, min_length=2, max_length=100)
    destination: str | None = Field(default=None, min_length=2, max_length=100)
    sort: TicketSort = TicketSort.PRICE_ASC
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class TicketResponse(BaseModel):
    trip_id: int
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    price: Decimal
    bus_model: str | None
    capacity: int
    available_seats: int


class RouteResponse(BaseModel):
    id: int
    origin: str
    destination: str


class TripSeatMapResponse(BaseModel):
    trip_id: int
    capacity: int
    unavailable_seats: list[int]


class BookingCreateRequest(BaseModel):
    trip_id: int = Field(gt=0)
    seat_number: int = Field(gt=0)


class BookingResponse(BaseModel):
    id: int
    trip_id: int
    seat_number: int
    paid_price: Decimal
    status: str
    booked_at: datetime
    remaining_wallet_balance: Decimal


class BookingCancellationResponse(BaseModel):
    id: int
    status: Literal["cancelled"]
    cancelled_at: datetime
    refunded_amount: Decimal
    remaining_wallet_balance: Decimal


class BookingListItemResponse(BaseModel):
    id: int
    trip_id: int
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    seat_number: int
    paid_price: Decimal
    status: Literal["confirmed", "cancelled"]
    booked_at: datetime
    cancelled_at: datetime | None
    bus_model: str | None


class BusImportItem(BaseModel):
    origin: str = Field(min_length=2, max_length=100)
    destination: str = Field(min_length=2, max_length=100)
    plate_number: str = Field(min_length=1, max_length=20)
    model: str | None = Field(default=None, max_length=100)
    capacity: int = Field(ge=1, le=100)


class BusImportRequest(BaseModel):
    buses: list[BusImportItem] = Field(min_length=1, max_length=1000)


class BusResponse(BaseModel):
    id: int
    origin: str
    destination: str
    plate_number: str
    model: str | None
    capacity: int
    is_active: bool


class BusImportResponse(BaseModel):
    imported_count: int
    buses: list[BusResponse]


class DriverResponse(BaseModel):
    id: int
    display_name: str
    mobile: str
    is_active: bool


class TripCreateRequest(BaseModel):
    bus_id: int = Field(gt=0)
    driver_profile_id: int = Field(gt=0)
    departure_time: datetime
    arrival_time: datetime
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class TripResponse(BaseModel):
    id: int
    bus_id: int
    driver_profile_id: int
    origin: str
    destination: str
    plate_number: str
    bus_model: str | None
    driver_name: str
    departure_time: datetime
    arrival_time: datetime
    price: Decimal
    status: Literal["scheduled"]


class OperatorTripResponse(BaseModel):
    id: int
    bus_id: int
    driver_profile_id: int
    origin: str
    destination: str
    plate_number: str
    bus_model: str | None
    driver_name: str
    departure_time: datetime
    arrival_time: datetime
    price: Decimal
    status: Literal["scheduled", "cancelled", "completed"]
    capacity: int
    available_seats: int


class HourlyBookingReportRow(BaseModel):
    hour: int = Field(ge=0, le=23)
    confirmed_bookings: int
    revenue: Decimal


class HourlyBookingReportResponse(BaseModel):
    report_date: date
    timezone: Literal["Asia/Tehran"] = "Asia/Tehran"
    total_confirmed_bookings: int
    total_revenue: Decimal
    hours: list[HourlyBookingReportRow]


class MonthlyBusReportRow(BaseModel):
    bus_id: int
    plate_number: str
    model: str | None
    trip_count: int
    confirmed_bookings: int
    revenue: Decimal


class MonthlyBusReportResponse(BaseModel):
    year: int
    month: int
    buses: list[MonthlyBusReportRow]


class BusiestDriverReportRow(BaseModel):
    driver_profile_id: int
    driver_name: str
    trip_count: int
    confirmed_bookings: int


class BusiestDriversReportResponse(BaseModel):
    date_from: date
    date_to: date
    drivers: list[BusiestDriverReportRow]
