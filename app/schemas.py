from typing import Literal
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from enum import Enum


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
    profiles: list[str]


class TicketSort(str, Enum):
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"


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
