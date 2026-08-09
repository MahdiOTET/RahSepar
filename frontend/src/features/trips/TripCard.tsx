import { ArrowLeft, BusFront, Clock3, UsersRound } from "lucide-react";

import {
  formatDate,
  formatDuration,
  formatNumber,
  formatPrice,
  formatTime,
} from "../../lib/format";
import type { Ticket } from "../../types/api";
import { IranRouteMap } from "./IranRouteMap";

interface TripCardProps {
  trip: Ticket;
  onSelect: (trip: Ticket) => void;
}

export function TripCard({ trip, onSelect }: TripCardProps) {
  return (
    <article className="trip-card">
      <div className="trip-card__topline">
        <span className="trip-card__date">
          {formatDate(trip.departure_time)}
        </span>
        <span className="trip-card__availability">
          <UsersRound size={16} aria-hidden="true" />
          {formatNumber(trip.available_seats)} صندلی خالی
        </span>
      </div>

      <div className="trip-card__route">
        <div className="trip-card__stop">
          <span className="trip-card__time" dir="ltr">
            {formatTime(trip.departure_time)}
          </span>
          <strong>{trip.origin}</strong>
        </div>
        <IranRouteMap origin={trip.origin} destination={trip.destination} />
        <div className="trip-card__stop trip-card__stop--destination">
          <span className="trip-card__time" dir="ltr">
            {formatTime(trip.arrival_time)}
          </span>
          <strong>{trip.destination}</strong>
        </div>
      </div>

      <div className="trip-card__meta">
        <span>
          <Clock3 size={17} aria-hidden="true" />
          <span>
            <strong className="trip-card__meta-label">مدت سفر:</strong>{" "}
            {formatDuration(trip.departure_time, trip.arrival_time)}
          </span>
        </span>
        <span>
          <BusFront size={17} aria-hidden="true" />
          {trip.bus_model ?? "اتوبوس بین‌شهری"}
        </span>
      </div>

      <div className="trip-card__footer">
        <div>
          <span className="trip-card__price-label">قیمت هر صندلی</span>
          <strong className="trip-card__price">
            {formatPrice(trip.price)}
          </strong>
        </div>
        <button
          className="button button--primary"
          type="button"
          onClick={() => onSelect(trip)}
        >
          انتخاب صندلی
          <ArrowLeft size={18} aria-hidden="true" />
        </button>
      </div>
    </article>
  );
}
