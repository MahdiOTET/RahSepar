import { useState } from "react";
import { Eye, EyeOff, LogIn, ShieldCheck } from "lucide-react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../../app/AuthContext";
import { StatusMessage } from "../../components/StatusMessage";
import { toPersianError } from "../../lib/format";

const DEMO_MOBILE = "09123456789";
const DEMO_PASSWORD = "DevPass123!";

function safeReturnPath(value: string | null): string {
  return value?.startsWith("/") && !value.startsWith("//") ? value : "/";
}

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (user) {
    return (
      <Navigate to={safeReturnPath(searchParams.get("returnTo"))} replace />
    );
  }

  return (
    <div className="auth-page page-container">
      <section className="auth-card" aria-labelledby="login-title">
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
            setSubmitting(true);
            setError("");
            void login(mobile, password)
              .then(() =>
                navigate(safeReturnPath(searchParams.get("returnTo")), {
                  replace: true,
                }),
              )
              .catch((reason: unknown) => setError(toPersianError(reason)))
              .finally(() => setSubmitting(false));
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
                onChange={(event) => setPassword(event.target.value)}
              />
              <button
                className="icon-button password-field__toggle"
                type="button"
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

        <aside className="demo-account">
          <div>
            <strong>حساب آماده برای نسخه نمایشی</strong>
            <span dir="ltr">
              {DEMO_MOBILE} · {DEMO_PASSWORD}
            </span>
          </div>
          <button
            className="button button--ghost"
            type="button"
            onClick={() => {
              setMobile(DEMO_MOBILE);
              setPassword(DEMO_PASSWORD);
            }}
          >
            تکمیل خودکار
          </button>
        </aside>
      </section>
    </div>
  );
}
