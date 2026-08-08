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
