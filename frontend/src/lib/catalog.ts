import { api } from "./api";
import type { RouteOption, Ticket } from "../types/api";

let routesPromise: Promise<RouteOption[]> | null = null;
let initialTicketsPromise: Promise<Ticket[]> | null = null;

function resetOnFailure<T>(promise: Promise<T>, reset: () => void): Promise<T> {
  return promise.catch((error: unknown) => {
    reset();
    throw error;
  });
}

export function loadRoutes(): Promise<RouteOption[]> {
  if (!routesPromise) {
    routesPromise = resetOnFailure(api.get<RouteOption[]>("/routes"), () => {
      routesPromise = null;
    });
  }
  return routesPromise;
}

export function loadInitialTickets(): Promise<Ticket[]> {
  if (!initialTicketsPromise) {
    initialTicketsPromise = resetOnFailure(
      api.get<Ticket[]>("/tickets?sort=price_asc&limit=20"),
      () => {
        initialTicketsPromise = null;
      },
    );
  }
  return initialTicketsPromise;
}

export function preloadHome(): Promise<unknown[]> {
  return Promise.all([loadRoutes(), loadInitialTickets()]);
}

export function invalidateInitialTickets(): void {
  initialTicketsPromise = null;
}
