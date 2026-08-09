import { useEffect, useState } from "react";
import { CalendarPlus, Plus, X } from "lucide-react";

import { LoadingState } from "../../components/LoadingState";
import { StatusMessage } from "../../components/StatusMessage";
import { api } from "../../lib/api";
import {
  formatDateTime,
  formatNumber,
  formatPrice,
  toPersianError,
  toTehranIso,
  tripStatusLabel,
} from "../../lib/format";
import type { Bus, Driver, OperatorTrip } from "../../types/api";

interface TripForm {
  bus_id: string;
  driver_profile_id: string;
  departure_time: string;
  arrival_time: string;
  price: string;
}

const emptyForm: TripForm = {
  bus_id: "",
  driver_profile_id: "",
  departure_time: "",
  arrival_time: "",
  price: "",
};

export function TripsPanel() {
  const [trips, setTrips] = useState<OperatorTrip[]>([]);
  const [buses, setBuses] = useState<Bus[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [form, setForm] = useState<TripForm>(emptyForm);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadData = async () => {
    const [tripRows, busRows, driverRows] = await Promise.all([
      api.get<OperatorTrip[]>("/trips?limit=100", true),
      api.get<Bus[]>("/buses?limit=200", true),
      api.get<Driver[]>("/drivers", true),
    ]);
    setTrips(tripRows);
    setBuses(busRows.filter((bus) => bus.is_active));
    setDrivers(driverRows.filter((driver) => driver.is_active));
  };

  useEffect(() => {
    void loadData()
      .catch((reason: unknown) => setError(toPersianError(reason)))
      .finally(() => setLoading(false));
  }, []);

  const createTrip = async () => {
    setSubmitting(true);
    setError("");
    try {
      await api.post(
        "/trips",
        {
          bus_id: Number(form.bus_id),
          driver_profile_id: Number(form.driver_profile_id),
          departure_time: toTehranIso(form.departure_time),
          arrival_time: toTehranIso(form.arrival_time),
          price: form.price,
        },
        true,
      );
      setNotice("سفر جدید با موفقیت برنامه‌ریزی شد.");
      setForm(emptyForm);
      setShowForm(false);
      await loadData();
    } catch (reason) {
      setError(toPersianError(reason));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="operator-section">
      <div className="operator-section__heading">
        <div>
          <h2>سفرها</h2>
          <p>برنامه سفرهای ثبت‌شده و ظرفیت باقی‌مانده.</p>
        </div>
        <button
          className="button button--primary"
          type="button"
          onClick={() => setShowForm((value) => !value)}
        >
          {showForm ? <X size={18} /> : <Plus size={18} />}
          {showForm ? "بستن فرم" : "برنامه‌ریزی سفر"}
        </button>
      </div>

      {notice && <StatusMessage type="success">{notice}</StatusMessage>}
      {error && <StatusMessage type="error">{error}</StatusMessage>}

      {showForm && (
        <form
          className="operator-form"
          onSubmit={(event) => {
            event.preventDefault();
            void createTrip();
          }}
        >
          <div className="form-field form-field--wide">
            <label htmlFor="trip-bus">اتوبوس و مسیر</label>
            <select
              id="trip-bus"
              required
              value={form.bus_id}
              onChange={(event) =>
                setForm({ ...form, bus_id: event.target.value })
              }
            >
              <option value="">انتخاب اتوبوس</option>
              {buses.map((bus) => (
                <option key={bus.id} value={bus.id}>
                  {bus.plate_number} · {bus.origin} به {bus.destination}
                </option>
              ))}
            </select>
          </div>
          <div className="form-field form-field--wide">
            <label htmlFor="trip-driver">راننده</label>
            <select
              id="trip-driver"
              required
              value={form.driver_profile_id}
              onChange={(event) =>
                setForm({ ...form, driver_profile_id: event.target.value })
              }
            >
              <option value="">انتخاب راننده</option>
              {drivers.map((driver) => (
                <option key={driver.id} value={driver.id}>
                  {driver.display_name}
                </option>
              ))}
            </select>
          </div>
          <div className="form-field">
            <label htmlFor="trip-departure">حرکت به وقت تهران</label>
            <input
              id="trip-departure"
              type="datetime-local"
              required
              value={form.departure_time}
              onChange={(event) =>
                setForm({ ...form, departure_time: event.target.value })
              }
            />
          </div>
          <div className="form-field">
            <label htmlFor="trip-arrival">رسیدن به وقت تهران</label>
            <input
              id="trip-arrival"
              type="datetime-local"
              required
              value={form.arrival_time}
              onChange={(event) =>
                setForm({ ...form, arrival_time: event.target.value })
              }
            />
          </div>
          <div className="form-field">
            <label htmlFor="trip-price">قیمت (تومان)</label>
            <input
              id="trip-price"
              type="number"
              min="1"
              step="1000"
              required
              value={form.price}
              onChange={(event) =>
                setForm({ ...form, price: event.target.value })
              }
            />
          </div>
          <button
            className="button button--accent"
            type="submit"
            disabled={submitting}
          >
            {submitting ? "در حال ثبت…" : "ثبت سفر"}
          </button>
        </form>
      )}

      {loading ? (
        <LoadingState />
      ) : (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>مسیر</th>
                <th>زمان حرکت</th>
                <th>اتوبوس</th>
                <th>راننده</th>
                <th>قیمت</th>
                <th>خالی</th>
                <th>وضعیت</th>
              </tr>
            </thead>
            <tbody>
              {trips.map((trip) => (
                <tr key={trip.id}>
                  <td>
                    {trip.origin} ← {trip.destination}
                  </td>
                  <td>{formatDateTime(trip.departure_time)}</td>
                  <td dir="ltr">{trip.plate_number}</td>
                  <td>{trip.driver_name}</td>
                  <td>{formatPrice(trip.price)}</td>
                  <td>{formatNumber(trip.available_seats)}</td>
                  <td>
                    <span
                      className={`status-badge status-badge--${trip.status === "scheduled" ? "confirmed" : "cancelled"}`}
                    >
                      {tripStatusLabel(trip.status)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {trips.length === 0 && (
            <div className="table-empty">
              <CalendarPlus size={24} /> سفری برنامه‌ریزی نشده است.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
