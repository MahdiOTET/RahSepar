import { useEffect, useRef } from "react";
import type { CSSProperties } from "react";

import type { Ticket } from "../../types/api";
import { TripCard } from "./TripCard";

interface TripListProps {
  tickets: Ticket[];
  onSelect: (trip: Ticket) => void;
}

export function TripList({ tickets, onSelect }: TripListProps) {
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const list = listRef.current;
    if (!list) return;

    const revealItems = Array.from(
      list.querySelectorAll<HTMLElement>("[data-trip-reveal]"),
    );
    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    if (
      revealItems.length === 0 ||
      reducedMotion ||
      typeof IntersectionObserver === "undefined"
    ) {
      return;
    }

    list.classList.add("trip-list--reveal-ready");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("trip-card-reveal--visible");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" },
    );

    revealItems.forEach((item) => observer.observe(item));

    return () => {
      observer.disconnect();
      list.classList.remove("trip-list--reveal-ready");
    };
  }, []);

  return (
    <div className="trip-list" ref={listRef}>
      {tickets.map((trip, index) => {
        const revealDelay = index < 6 ? index * 40 : 0;
        return (
          <div
            className="trip-card-reveal"
            data-trip-reveal
            key={trip.trip_id}
            style={
              {
                "--trip-reveal-delay": `${revealDelay}ms`,
              } as CSSProperties
            }
          >
            <TripCard trip={trip} onSelect={onSelect} />
          </div>
        );
      })}
    </div>
  );
}
