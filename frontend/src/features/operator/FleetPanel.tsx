import { useCallback, useEffect, useState } from "react";
import { BusFront, Plus, X } from "lucide-react";

import { LoadingState } from "../../components/LoadingState";
import { StatusMessage } from "../../components/StatusMessage";
import { api } from "../../lib/api";
import { formatNumber, toPersianError } from "../../lib/format";
import type { Bus, BusImportResponse } from "../../types/api";

interface BusForm {
  origin: string;
  destination: string;
  plate_number: string;
  model: string;
  capacity: string;
}

const emptyForm: BusForm = {
  origin: "",
  destination: "",
  plate_number: "",
  model: "",
  capacity: "40",
};

export function FleetPanel() {
  const [buses, setBuses] = useState<Bus[]>([]);
  const [form, setForm] = useState<BusForm>(emptyForm);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadBuses = useCallback(async () => {
    const result = await api.get<Bus[]>("/buses?limit=200", true);
    setBuses(result);
  }, []);

  useEffect(() => {
    void loadBuses()
      .catch((reason: unknown) => setError(toPersianError(reason)))
      .finally(() => setLoading(false));
  }, [loadBuses]);

  const submit = async () => {
    setSubmitting(true);
    setError("");
    try {
      const result = await api.post<BusImportResponse>(
        "/buses",
        {
          buses: [
            {
              ...form,
              origin: form.origin.trim(),
              destination: form.destination.trim(),
              plate_number: form.plate_number.trim(),
              model: form.model.trim() || null,
              capacity: Number(form.capacity),
            },
          ],
        },
        true,
      );
      setNotice(
        `اتوبوس ${result.buses[0]?.plate_number ?? "جدید"} با موفقیت ثبت شد.`,
      );
      setForm(emptyForm);
      setShowForm(false);
      await loadBuses();
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
          <h2>ناوگان</h2>
          <p>اتوبوس‌های فعال و مسیر اختصاص‌یافته به هرکدام.</p>
        </div>
        <button
          className="button button--primary"
          type="button"
          onClick={() => setShowForm((value) => !value)}
        >
          {showForm ? <X size={18} /> : <Plus size={18} />}
          {showForm ? "بستن فرم" : "افزودن اتوبوس"}
        </button>
      </div>

      {notice && <StatusMessage type="success">{notice}</StatusMessage>}
      {error && <StatusMessage type="error">{error}</StatusMessage>}

      {showForm && (
        <form
          className="operator-form"
          onSubmit={(event) => {
            event.preventDefault();
            void submit();
          }}
        >
          <div className="form-field">
            <label htmlFor="bus-origin">مبدأ</label>
            <input
              id="bus-origin"
              value={form.origin}
              required
              minLength={2}
              onChange={(event) =>
                setForm({ ...form, origin: event.target.value })
              }
            />
          </div>
          <div className="form-field">
            <label htmlFor="bus-destination">مقصد</label>
            <input
              id="bus-destination"
              value={form.destination}
              required
              minLength={2}
              onChange={(event) =>
                setForm({ ...form, destination: event.target.value })
              }
            />
          </div>
          <div className="form-field">
            <label htmlFor="bus-plate">شماره پلاک</label>
            <input
              id="bus-plate"
              dir="ltr"
              value={form.plate_number}
              required
              onChange={(event) =>
                setForm({ ...form, plate_number: event.target.value })
              }
            />
          </div>
          <div className="form-field">
            <label htmlFor="bus-model">مدل</label>
            <input
              id="bus-model"
              value={form.model}
              onChange={(event) =>
                setForm({ ...form, model: event.target.value })
              }
            />
          </div>
          <div className="form-field">
            <label htmlFor="bus-capacity">ظرفیت</label>
            <input
              id="bus-capacity"
              type="number"
              min="1"
              max="100"
              value={form.capacity}
              required
              onChange={(event) =>
                setForm({ ...form, capacity: event.target.value })
              }
            />
          </div>
          <button
            className="button button--accent"
            type="submit"
            disabled={submitting}
          >
            {submitting ? "در حال ثبت…" : "ثبت اتوبوس"}
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
                <th>پلاک</th>
                <th>مدل</th>
                <th>مسیر</th>
                <th>ظرفیت</th>
                <th>وضعیت</th>
              </tr>
            </thead>
            <tbody>
              {buses.map((bus) => (
                <tr key={bus.id}>
                  <td dir="ltr">{bus.plate_number}</td>
                  <td>{bus.model ?? "—"}</td>
                  <td>
                    {bus.origin} ← {bus.destination}
                  </td>
                  <td>{formatNumber(bus.capacity)}</td>
                  <td>
                    <span
                      className={`status-badge status-badge--${bus.is_active ? "confirmed" : "cancelled"}`}
                    >
                      {bus.is_active ? "فعال" : "غیرفعال"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {buses.length === 0 && (
            <div className="table-empty">
              <BusFront size={24} /> اتوبوسی ثبت نشده است.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
