import { useEffect, useRef, useState } from "react";
import { Armchair, Check, X } from "lucide-react";

import { api } from "../../lib/api";
import { formatNumber, formatPrice, toPersianError } from "../../lib/format";
import type { BookingResult, Ticket, TripSeatMap } from "../../types/api";
import { LoadingState } from "../../components/LoadingState";
import { StatusMessage } from "../../components/StatusMessage";

interface SeatPickerProps {
  trip: Ticket;
  onClose: () => void;
  onBooked: (booking: BookingResult) => void;
}

export function SeatPicker({ trip, onClose, onBooked }: SeatPickerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [seatMap, setSeatMap] = useState<TripSeatMap | null>(null);
  const [selectedSeat, setSelectedSeat] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) {
      dialog.showModal();
    }
    return () => dialog?.close();
  }, []);

  useEffect(() => {
    let active = true;
    api
      .get<TripSeatMap>(`/trips/${trip.trip_id}/seats`)
      .then((result) => {
        if (active) setSeatMap(result);
      })
      .catch((reason: unknown) => {
        if (active) setError(toPersianError(reason));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [trip.trip_id]);

  const submitBooking = async () => {
    if (!selectedSeat) return;
    setSubmitting(true);
    setError("");
    try {
      const booking = await api.post<BookingResult>(
        "/bookings",
        { trip_id: trip.trip_id, seat_number: selectedSeat },
        true,
      );
      onBooked(booking);
    } catch (reason) {
      setError(toPersianError(reason));
      if (
        reason instanceof Error &&
        reason.message === "Seat is already booked"
      ) {
        const refreshedMap = await api.get<TripSeatMap>(
          `/trips/${trip.trip_id}/seats`,
        );
        setSeatMap(refreshedMap);
        setSelectedSeat(null);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const unavailable = new Set(seatMap?.unavailable_seats ?? []);

  return (
    <dialog
      ref={dialogRef}
      className="seat-dialog"
      aria-labelledby="seat-dialog-title"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="seat-dialog__panel">
        <div className="seat-dialog__header">
          <div>
            <span className="eyebrow">
              {trip.origin} به {trip.destination}
            </span>
            <h2 id="seat-dialog-title">صندلی خود را انتخاب کنید</h2>
          </div>
          <button
            className="icon-button"
            type="button"
            onClick={onClose}
            aria-label="بستن"
          >
            <X size={21} />
          </button>
        </div>

        {loading && <LoadingState label="در حال دریافت صندلی‌ها…" />}
        {error && <StatusMessage type="error">{error}</StatusMessage>}

        {seatMap && (
          <>
            <div className="seat-legend" aria-label="راهنمای وضعیت صندلی‌ها">
              <span>
                <i className="seat-legend__sample" /> آزاد
              </span>
              <span>
                <i className="seat-legend__sample seat-legend__sample--selected" />{" "}
                انتخاب شما
              </span>
              <span>
                <i className="seat-legend__sample seat-legend__sample--unavailable" />{" "}
                رزروشده
              </span>
            </div>
            <div
              className="seat-map"
              role="group"
              aria-label="صندلی‌های اتوبوس"
            >
              <span className="seat-map__driver" aria-hidden="true">
                <Armchair size={19} /> راننده
              </span>
              <div className="seat-map__grid">
                {Array.from(
                  { length: seatMap.capacity },
                  (_, index) => index + 1,
                ).map((seat) => {
                  const isUnavailable = unavailable.has(seat);
                  const isSelected = selectedSeat === seat;
                  return (
                    <button
                      key={seat}
                      type="button"
                      className={`seat${isSelected ? " seat--selected" : ""}`}
                      disabled={isUnavailable}
                      aria-pressed={isSelected}
                      aria-label={`صندلی ${formatNumber(seat)}${isUnavailable ? "، رزرو شده" : ""}`}
                      onClick={() => setSelectedSeat(seat)}
                    >
                      {isSelected ? (
                        <Check size={17} aria-hidden="true" />
                      ) : (
                        formatNumber(seat)
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        )}

        <div className="seat-dialog__footer">
          <div>
            <span>
              {selectedSeat
                ? `صندلی ${formatNumber(selectedSeat)}`
                : "هنوز صندلی انتخاب نشده"}
            </span>
            <strong>{formatPrice(trip.price)}</strong>
          </div>
          <button
            className="button button--primary"
            type="button"
            disabled={!selectedSeat || submitting}
            onClick={submitBooking}
          >
            {submitting ? "در حال ثبت…" : "تأیید و پرداخت از کیف پول"}
          </button>
        </div>
      </div>
    </dialog>
  );
}
