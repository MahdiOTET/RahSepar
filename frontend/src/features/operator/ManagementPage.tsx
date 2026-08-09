import { useState } from "react";
import { BarChart3, BusFront, CalendarPlus } from "lucide-react";

import { FleetPanel } from "./FleetPanel";
import { ReportsPanel } from "./ReportsPanel";
import { TripsPanel } from "./TripsPanel";

type ManagementTab = "trips" | "fleet" | "reports";

export default function ManagementPage() {
  const [tab, setTab] = useState<ManagementTab>("trips");

  return (
    <div className="management-page page-container">
      <header className="page-title">
        <span className="eyebrow">مدیریت راه‌سپار</span>
        <h1>عملیات سامانه</h1>
        <p>سفرها، ناوگان و گزارش‌ها؛ هرکدام در جای مشخص خود.</p>
      </header>

      <div className="management-tabs" role="tablist" aria-label="بخش مدیریت">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "trips"}
          onClick={() => setTab("trips")}
        >
          <CalendarPlus size={19} /> سفرها
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "fleet"}
          onClick={() => setTab("fleet")}
        >
          <BusFront size={19} /> ناوگان
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "reports"}
          onClick={() => setTab("reports")}
        >
          <BarChart3 size={19} /> گزارش‌ها
        </button>
      </div>

      <section className="management-panel" role="tabpanel">
        {tab === "trips" && <TripsPanel />}
        {tab === "fleet" && <FleetPanel />}
        {tab === "reports" && <ReportsPanel />}
      </section>
    </div>
  );
}
