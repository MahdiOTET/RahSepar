import { useState } from "react";
import { Eye, EyeOff, LogIn, ShieldCheck, UserRound } from "lucide-react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../../app/AuthContext";
import { StatusMessage } from "../../components/StatusMessage";
import { toPersianError } from "../../lib/format";

const DEMO_PASSWORD = "DevPass123!";
const DEMO_ACCOUNTS = [
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

type DemoAccountId = (typeof DEMO_ACCOUNTS)[number]["id"];

function safeReturnPath(value: string | null): string | null {
  return value?.startsWith("/") && !value.startsWith("//") ? value : null;
}

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [activeDemo, setActiveDemo] = useState<DemoAccountId | null>(null);
  const [error, setError] = useState("");
  const requestedReturnPath = safeReturnPath(searchParams.get("returnTo"));

  const authenticate = async (
    nextMobile: string,
    nextPassword: string,
    defaultPath: string,
    demoId: DemoAccountId | null = null,
  ) => {
    setMobile(nextMobile);
    setPassword(nextPassword);
    setSubmitting(true);
    setActiveDemo(demoId);
    setError("");

    try {
      await login(nextMobile, nextPassword);
      navigate(requestedReturnPath ?? defaultPath, { replace: true });
    } catch (reason) {
      setError(toPersianError(reason));
    } finally {
      setSubmitting(false);
      setActiveDemo(null);
    }
  };

  if (user) {
    return <Navigate to={requestedReturnPath ?? "/"} replace />;
  }

  return (
    <div className="auth-page page-container">
      <section
        className="auth-card"
        aria-labelledby="login-title"
        aria-busy={submitting}
      >
        <div className="auth-card__intro">
          <span className="auth-card__icon">
            <ShieldCheck size={25} />
          </span>
          <span className="eyebrow">خوش آمدید</span>
          <h1 id="login-title">ورود به راه‌سپار</h1>
          <p>برای رزرو صندلی، مشاهده سفرها و مدیریت حساب وارد شوید.</p>
        </div>

        {error && <StatusMessage type="error">{error}</StatusMessage>}

        <form
          className="stack-form"
          onSubmit={(event) => {
            event.preventDefault();
            void authenticate(mobile, password, "/");
          }}
        >
          <div className="form-field">
            <label htmlFor="mobile">شماره موبایل</label>
            <input
              id="mobile"
              name="mobile"
              type="tel"
              inputMode="numeric"
              autoComplete="username"
              dir="ltr"
              value={mobile}
              pattern="\+?[0-9]+"
              minLength={10}
              maxLength={15}
              required
              disabled={submitting}
              onChange={(event) => setMobile(event.target.value.trim())}
            />
          </div>
          <div className="form-field">
            <label htmlFor="password">رمز عبور</label>
            <div className="password-field">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                dir="ltr"
                value={password}
                minLength={8}
                required
                disabled={submitting}
                onChange={(event) => setPassword(event.target.value)}
              />
              <button
                className="icon-button password-field__toggle"
                type="button"
                disabled={submitting}
                onClick={() => setShowPassword((current) => !current)}
                aria-label={
                  showPassword ? "پنهان‌کردن رمز عبور" : "نمایش رمز عبور"
                }
              >
                {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
              </button>
            </div>
          </div>
          <button
            className="button button--primary button--wide"
            type="submit"
            disabled={submitting}
          >
            <LogIn size={19} aria-hidden="true" />
            {submitting ? "در حال ورود…" : "ورود به حساب"}
          </button>
        </form>

        <aside className="demo-accounts" aria-labelledby="demo-accounts-title">
          <div className="demo-accounts__heading">
            <span className="eyebrow">ورود سریع</span>
            <h2 id="demo-accounts-title">یک حساب نمایشی انتخاب کنید</h2>
          </div>
          <div className="demo-accounts__list">
            {DEMO_ACCOUNTS.map((account) => {
              const Icon = account.id === "passenger" ? UserRound : ShieldCheck;
              const isActive = activeDemo === account.id;

              return (
                <button
                  className="demo-account-option"
                  type="button"
                  key={account.id}
                  disabled={submitting}
                  onClick={() =>
                    void authenticate(
                      account.mobile,
                      DEMO_PASSWORD,
                      account.defaultPath,
                      account.id,
                    )
                  }
                >
                  <span className="demo-account-option__icon">
                    <Icon size={20} aria-hidden="true" />
                  </span>
                  <span className="demo-account-option__copy">
                    <strong>{account.label}</strong>
                    <span>{account.description}</span>
                    <span dir="ltr">{account.mobile}</span>
                  </span>
                  <span className="demo-account-option__action">
                    {isActive ? "در حال ورود…" : "ورود سریع"}
                  </span>
                </button>
              );
            })}
          </div>
          <p className="demo-accounts__note">
            رمز هر دو حساب <span dir="ltr">{DEMO_PASSWORD}</span> است. اطلاعات
            این محیط نمایشی و میان بازدیدکنندگان مشترک است.
          </p>
        </aside>
      </section>
    </div>
  );
}
