import type { RefObject } from "react";
import { BusFront } from "lucide-react";

import { EmptyState } from "../../components/EmptyState";
import { LoadingState } from "../../components/LoadingState";
import { formatNumber } from "../../lib/format";
import type { Ticket, TicketSort } from "../../types/api";
import { TripList } from "./TripList";

interface TripResultsProps {
  headingRef: RefObject<HTMLDivElement | null>;
  loading: boolean;
  searched: boolean;
  origin: string;
  destination: string;
  sort: TicketSort;
  tickets: Ticket[];
  resultRevision: number;
  onSortChange: (sort: TicketSort) => void;
  onSelect: (trip: Ticket) => void;
}

const SORT_OPTIONS: Array<{ value: TicketSort; label: string }> = [
  { value: "price_asc", label: "ارزان‌ترین" },
  { value: "price_desc", label: "گران‌ترین" },
  { value: "departure_asc", label: "زودترین حرکت" },
  { value: "departure_desc", label: "دیرترین حرکت" },
];

export function TripResults({
  headingRef,
  loading,
  searched,
  origin,
  destination,
  sort,
  tickets,
  resultRevision,
  onSortChange,
  onSelect,
}: TripResultsProps) {
  return (
    <section
      className="trip-results"
      aria-labelledby="trip-results-title"
      aria-busy={loading}
    >
      <div className="section-heading trip-results__heading" ref={headingRef}>
        <div>
          <span className="eyebrow">
            {searched ? "نتیجه جست‌وجو" : "پیشنهادهای آماده"}
          </span>
          <h2 id="trip-results-title">
            {searched ? `${origin} به ${destination}` : "سفرهای پیش رو"}
          </h2>
          {!loading && (
            <p aria-live="polite" aria-atomic="true">
              {formatNumber(tickets.length)} سفر در دسترس
            </p>
          )}
        </div>
        <div className="sort-control">
          <label htmlFor="trip-sort">مرتب‌سازی سفرها</label>
          <select
            id="trip-sort"
            value={sort}
            disabled={loading}
            onChange={(event) => onSortChange(event.target.value as TicketSort)}
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <LoadingState label="در حال یافتن سفرها…" />
      ) : tickets.length > 0 ? (
        <TripList key={resultRevision} tickets={tickets} onSelect={onSelect} />
      ) : (
        <EmptyState
          icon={BusFront}
          title="برای این مسیر سفری پیدا نشد"
          description="مسیر دیگری را امتحان کنید یا کمی بعد دوباره برگردید."
        />
      )}
    </section>
  );
}
