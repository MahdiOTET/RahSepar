from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class TicketSearchCriteria:
    origin: str | None
    destination: str | None
    sort: str
    limit: int
    offset: int


@dataclass(frozen=True)
class TripSchedule:
    bus_id: int
    driver_profile_id: int
    departure_time: datetime
    arrival_time: datetime
    price: Decimal
