export type ProfileType = "passenger" | "operator" | "driver";
export type TripStatus = "scheduled" | "cancelled" | "completed";
export type BookingStatus = "confirmed" | "cancelled";
export type TicketSort =
  "price_asc" | "price_desc" | "departure_asc" | "departure_desc";

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

export interface CurrentUser {
  id: number;
  mobile: string;
  display_name: string;
  wallet_balance: string;
  profiles: ProfileType[];
}

export interface RouteOption {
  id: number;
  origin: string;
  destination: string;
}

export interface Ticket {
  trip_id: number;
  origin: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  price: string;
  bus_model: string | null;
  capacity: number;
  available_seats: number;
}

export interface TripSeatMap {
  trip_id: number;
  capacity: number;
  unavailable_seats: number[];
}

export interface BookingResult {
  id: number;
  trip_id: number;
  seat_number: number;
  paid_price: string;
  status: BookingStatus;
  booked_at: string;
  remaining_wallet_balance: string;
}

export interface BookingListItem {
  id: number;
  trip_id: number;
  origin: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  seat_number: number;
  paid_price: string;
  status: BookingStatus;
  booked_at: string;
  cancelled_at: string | null;
  bus_model: string | null;
}

export interface BookingCancellation {
  id: number;
  status: "cancelled";
  cancelled_at: string;
  refunded_amount: string;
  remaining_wallet_balance: string;
}

export interface Bus {
  id: number;
  origin: string;
  destination: string;
  plate_number: string;
  model: string | null;
  capacity: number;
  is_active: boolean;
}

export interface BusImportResponse {
  imported_count: number;
  buses: Bus[];
}

export interface Driver {
  id: number;
  display_name: string;
  mobile: string;
  is_active: boolean;
}

export interface OperatorTrip {
  id: number;
  bus_id: number;
  driver_profile_id: number;
  origin: string;
  destination: string;
  plate_number: string;
  bus_model: string | null;
  driver_name: string;
  departure_time: string;
  arrival_time: string;
  price: string;
  status: TripStatus;
  capacity: number;
  available_seats: number;
}

export interface HourlyReportRow {
  hour: number;
  confirmed_bookings: number;
  revenue: string;
}

export interface HourlyReport {
  report_date: string;
  timezone: "Asia/Tehran";
  total_confirmed_bookings: number;
  total_revenue: string;
  hours: HourlyReportRow[];
}

export interface MonthlyBusReportRow {
  bus_id: number;
  plate_number: string;
  model: string | null;
  trip_count: number;
  confirmed_bookings: number;
  revenue: string;
}

export interface MonthlyBusReport {
  year: number;
  month: number;
  buses: MonthlyBusReportRow[];
}

export interface BusiestDriverReportRow {
  driver_profile_id: number;
  driver_name: string;
  trip_count: number;
  confirmed_bookings: number;
}

export interface BusiestDriversReport {
  date_from: string;
  date_to: string;
  drivers: BusiestDriverReportRow[];
}
