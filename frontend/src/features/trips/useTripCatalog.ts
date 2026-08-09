import { useCallback, useEffect, useState } from "react";

import { api, toQueryString } from "../../lib/api";
import { loadInitialTickets, loadRoutes } from "../../lib/catalog";
import { toPersianError } from "../../lib/format";
import type { RouteOption, Ticket, TicketSort } from "../../types/api";

interface TicketCriteria {
  origin: string;
  destination: string;
  sort: TicketSort;
}

interface LoadTicketOptions {
  animate?: boolean;
}

export function useTripCatalog() {
  const [routes, setRoutes] = useState<RouteOption[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const [resultRevision, setResultRevision] = useState(0);

  useEffect(() => {
    let active = true;

    Promise.all([loadRoutes(), loadInitialTickets()])
      .then(([routeOptions, initialTickets]) => {
        if (!active) return;
        setRoutes(routeOptions);
        setTickets(initialTickets);
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
  }, []);

  const loadTickets = useCallback(
    async (
      { origin, destination, sort }: TicketCriteria,
      { animate = true }: LoadTicketOptions = {},
    ): Promise<boolean> => {
      setLoading(true);
      setError("");

      try {
        const result = await api.get<Ticket[]>(
          `/tickets${toQueryString({ origin, destination, sort, limit: 100 })}`,
        );
        setTickets(result);
        setSearched(Boolean(origin || destination));
        if (animate) setResultRevision((current) => current + 1);
        return true;
      } catch (reason) {
        setError(toPersianError(reason));
        return false;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  return {
    routes,
    tickets,
    loading,
    error,
    searched,
    resultRevision,
    loadTickets,
  };
}
