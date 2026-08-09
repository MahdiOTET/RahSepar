export const DEMO_PASSWORD = "DevPass123!";

export const DEMO_ACCOUNTS = [
  {
    id: "passenger",
    label: "مسافر نمایشی",
    description: "رزرو و مشاهده سفرهای من",
    mobile: "09800000001",
    defaultPath: "/bookings",
  },
  {
    id: "operator",
    label: "اپراتور سامانه",
    description: "مدیریت ناوگان، سفرها و گزارش‌ها",
    mobile: "09123456789",
    defaultPath: "/manage",
  },
] as const;

export type DemoAccount = (typeof DEMO_ACCOUNTS)[number];
export type DemoAccountId = DemoAccount["id"];
