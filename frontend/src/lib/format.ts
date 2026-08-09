import type { BookingStatus, ProfileType, TripStatus } from "../types/api";

const dateTimeFormatter = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Asia/Tehran",
});

const dateFormatter = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
  weekday: "long",
  day: "numeric",
  month: "long",
  timeZone: "Asia/Tehran",
});

const timeFormatter = new Intl.DateTimeFormat("fa-IR", {
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZone: "Asia/Tehran",
});

const numberFormatter = new Intl.NumberFormat("fa-IR");

export function formatDateTime(value: string): string {
  return dateTimeFormatter.format(new Date(value));
}

export function formatDate(value: string): string {
  return dateFormatter.format(new Date(value));
}

export function formatTime(value: string): string {
  return timeFormatter.format(new Date(value));
}

export function formatNumber(value: number | string): string {
  return numberFormatter.format(Number(value));
}

export function formatPrice(value: number | string): string {
  return `${formatNumber(value)} تومان`;
}

export function formatDuration(start: string, end: string): string {
  const minutes = Math.max(
    0,
    Math.round((new Date(end).getTime() - new Date(start).getTime()) / 60_000),
  );
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  if (remainder === 0) {
    return `${formatNumber(hours)} ساعت`;
  }
  return `${formatNumber(hours)} ساعت و ${formatNumber(remainder)} دقیقه`;
}

export function profileLabel(profile: ProfileType): string {
  const labels: Record<ProfileType, string> = {
    passenger: "مسافر",
    operator: "مدیر سامانه",
    driver: "راننده",
  };
  return labels[profile];
}

export function bookingStatusLabel(status: BookingStatus): string {
  return status === "confirmed" ? "تأییدشده" : "لغوشده";
}

export function tripStatusLabel(status: TripStatus): string {
  const labels: Record<TripStatus, string> = {
    scheduled: "برنامه‌ریزی‌شده",
    cancelled: "لغوشده",
    completed: "انجام‌شده",
  };
  return labels[status];
}

export function toTehranIso(localDateTime: string): string {
  const value =
    localDateTime.length === 16 ? `${localDateTime}:00` : localDateTime;
  return `${value}+03:30`;
}

export function todayIsoDate(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function toPersianError(error: unknown): string {
  if (!(error instanceof Error)) {
    return "خطای پیش‌بینی‌نشده‌ای رخ داد.";
  }

  const translations: Record<string, string> = {
    "Invalid Mobile or Password": "شماره موبایل یا رمز عبور درست نیست.",
    "Seat is already booked":
      "این صندلی همین حالا رزرو شده است. صندلی دیگری انتخاب کنید.",
    "Insufficient wallet balance": "موجودی کیف پول برای این رزرو کافی نیست.",
    "Daily booking limit has been reached":
      "سقف روزانه ۲۰ رزرو شما تکمیل شده است.",
    "Trip is not available for booking":
      "این سفر دیگر برای رزرو در دسترس نیست.",
    "Operator profile is required": "دسترسی مدیر سامانه لازم است.",
  };
  return translations[error.message] ?? error.message;
}
