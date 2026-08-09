import { useState } from "react";
import { BarChart3, BusFront, Clock3, UsersRound } from "lucide-react";

import { LoadingState } from "../../components/LoadingState";
import { StatusMessage } from "../../components/StatusMessage";
import { api, toQueryString } from "../../lib/api";
import {
  formatNumber,
  formatPrice,
  todayIsoDate,
  toPersianError,
} from "../../lib/format";
import type {
  BusiestDriversReport,
  HourlyReport,
  MonthlyBusReport,
} from "../../types/api";

type ReportType = "hourly" | "monthly" | "drivers";

export function ReportsPanel() {
  const today = todayIsoDate();
  const [type, setType] = useState<ReportType>("hourly");
  const [reportDate, setReportDate] = useState(today);
  const [month, setMonth] = useState(today.slice(0, 7));
  const [dateFrom, setDateFrom] = useState(today);
  const [dateTo, setDateTo] = useState(today);
  const [hourly, setHourly] = useState<HourlyReport | null>(null);
  const [monthly, setMonthly] = useState<MonthlyBusReport | null>(null);
  const [drivers, setDrivers] = useState<BusiestDriversReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runReport = async () => {
    setLoading(true);
    setError("");
    try {
      if (type === "hourly") {
        setHourly(
          await api.get<HourlyReport>(
            `/reports/hourly-bookings${toQueryString({ report_date: reportDate })}`,
            true,
          ),
        );
      } else if (type === "monthly") {
        const [year, selectedMonth] = month.split("-").map(Number);
        setMonthly(
          await api.get<MonthlyBusReport>(
            `/reports/monthly-buses${toQueryString({ year, month: selectedMonth })}`,
            true,
          ),
        );
      } else {
        setDrivers(
          await api.get<BusiestDriversReport>(
            `/reports/busiest-drivers${toQueryString({ date_from: dateFrom, date_to: dateTo, limit: 20 })}`,
            true,
          ),
        );
      }
    } catch (reason) {
      setError(toPersianError(reason));
    } finally {
      setLoading(false);
    }
  };

  const visibleHourlyRows =
    hourly?.hours.filter((row) => row.confirmed_bookings > 0) ?? [];

  return (
    <div className="operator-section">
      <div className="operator-section__heading">
        <div>
          <h2>گزارش‌ها</h2>
          <p>یک گزارش را انتخاب کنید و فقط داده موردنیاز را ببینید.</p>
        </div>
      </div>

      <div className="report-type" role="tablist" aria-label="نوع گزارش">
        <button
          type="button"
          aria-selected={type === "hourly"}
          onClick={() => setType("hourly")}
        >
          <Clock3 size={18} /> رزرو ساعتی
        </button>
        <button
          type="button"
          aria-selected={type === "monthly"}
          onClick={() => setType("monthly")}
        >
          <BusFront size={18} /> عملکرد اتوبوس
        </button>
        <button
          type="button"
          aria-selected={type === "drivers"}
          onClick={() => setType("drivers")}
        >
          <UsersRound size={18} /> رانندگان پرتردد
        </button>
      </div>

      <form
        className="report-form"
        onSubmit={(event) => {
          event.preventDefault();
          void runReport();
        }}
      >
        {type === "hourly" && (
          <div className="form-field">
            <label htmlFor="report-date">تاریخ گزارش</label>
            <input
              id="report-date"
              type="date"
              value={reportDate}
              required
              onChange={(event) => setReportDate(event.target.value)}
            />
          </div>
        )}
        {type === "monthly" && (
          <div className="form-field">
            <label htmlFor="report-month">ماه گزارش</label>
            <input
              id="report-month"
              type="month"
              value={month}
              required
              onChange={(event) => setMonth(event.target.value)}
            />
          </div>
        )}
        {type === "drivers" && (
          <>
            <div className="form-field">
              <label htmlFor="date-from">از تاریخ</label>
              <input
                id="date-from"
                type="date"
                value={dateFrom}
                required
                onChange={(event) => setDateFrom(event.target.value)}
              />
            </div>
            <div className="form-field">
              <label htmlFor="date-to">تا تاریخ</label>
              <input
                id="date-to"
                type="date"
                value={dateTo}
                required
                onChange={(event) => setDateTo(event.target.value)}
              />
            </div>
          </>
        )}
        <button
          className="button button--accent"
          type="submit"
          disabled={loading}
        >
          <BarChart3 size={18} /> {loading ? "در حال تهیه…" : "نمایش گزارش"}
        </button>
      </form>

      {error && <StatusMessage type="error">{error}</StatusMessage>}
      {loading && <LoadingState label="در حال محاسبه گزارش…" />}

      {!loading && type === "hourly" && hourly && (
        <div className="report-result">
          <div className="report-summary">
            <div>
              <span>کل رزروها</span>
              <strong>{formatNumber(hourly.total_confirmed_bookings)}</strong>
            </div>
            <div>
              <span>درآمد</span>
              <strong>{formatPrice(hourly.total_revenue)}</strong>
            </div>
          </div>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ساعت تهران</th>
                  <th>رزرو</th>
                  <th>درآمد</th>
                </tr>
              </thead>
              <tbody>
                {visibleHourlyRows.map((row) => (
                  <tr key={row.hour}>
                    <td>{formatNumber(row.hour)}:۰۰</td>
                    <td>{formatNumber(row.confirmed_bookings)}</td>
                    <td>{formatPrice(row.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {visibleHourlyRows.length === 0 && (
              <div className="table-empty">
                در این تاریخ رزروی ثبت نشده است.
              </div>
            )}
          </div>
        </div>
      )}
      {!loading && type === "monthly" && monthly && (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>پلاک</th>
                <th>مدل</th>
                <th>سفر</th>
                <th>رزرو</th>
                <th>درآمد</th>
              </tr>
            </thead>
            <tbody>
              {monthly.buses.map((bus) => (
                <tr key={bus.bus_id}>
                  <td dir="ltr">{bus.plate_number}</td>
                  <td>{bus.model ?? "—"}</td>
                  <td>{formatNumber(bus.trip_count)}</td>
                  <td>{formatNumber(bus.confirmed_bookings)}</td>
                  <td>{formatPrice(bus.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {!loading && type === "drivers" && drivers && (
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>راننده</th>
                <th>تعداد سفر</th>
                <th>رزرو تأییدشده</th>
              </tr>
            </thead>
            <tbody>
              {drivers.drivers.map((driver) => (
                <tr key={driver.driver_profile_id}>
                  <td>{driver.driver_name}</td>
                  <td>{formatNumber(driver.trip_count)}</td>
                  <td>{formatNumber(driver.confirmed_bookings)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {drivers.drivers.length === 0 && (
            <div className="table-empty">در این بازه سفری ثبت نشده است.</div>
          )}
        </div>
      )}
    </div>
  );
}
