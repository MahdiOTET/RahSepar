import { useEffect, useRef } from "react";
import type { CSSProperties, RefObject } from "react";

import type { Ticket } from "../../types/api";
import { TripCard } from "./TripCard";

interface TripListProps {
  tickets: Ticket[];
  onSelect: (trip: Ticket) => void;
}

type RevealStyle = CSSProperties & { "--trip-reveal-delay": string };

function useCardReveal(listRef: RefObject<HTMLDivElement | null>): void {
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
  }, [listRef]);
}

function revealDelay(index: number): RevealStyle {
  return {
    "--trip-reveal-delay": `${index < 6 ? index * 40 : 0}ms`,
  };
}

export function TripList({ tickets, onSelect }: TripListProps) {
  const listRef = useRef<HTMLDivElement>(null);
  useCardReveal(listRef);

  return (
    <div className="trip-list" ref={listRef}>
      {tickets.map((trip, index) => (
        <div
          className="trip-card-reveal"
          data-trip-reveal
          key={trip.trip_id}
          style={revealDelay(index)}
        >
          <TripCard trip={trip} onSelect={onSelect} />
        </div>
      ))}
    </div>
  );
}
