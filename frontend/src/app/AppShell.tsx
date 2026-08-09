import {
  BusFront,
  ClipboardList,
  LogIn,
  Moon,
  Settings,
  Sun,
  UserRound,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "./AuthContext";
import { useTheme } from "./ThemeContext";
import { BrandMark } from "../components/BrandMark";

const navClass = ({ isActive }: { isActive: boolean }) =>
  `app-nav__link${isActive ? " app-nav__link--active" : ""}`;

export function AppShell() {
  const { user, isOperator } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        رفتن به محتوای اصلی
      </a>
      <header className="app-header">
        <div className="app-header__inner">
          <NavLink to="/" aria-label="صفحه سفرها" className="app-header__brand">
            <BrandMark compact />
          </NavLink>
          <nav className="app-nav app-nav--desktop" aria-label="ناوبری اصلی">
            <NavLink to="/" end className={navClass}>
              سفرها
            </NavLink>
            <NavLink to="/bookings" className={navClass}>
              رزروهای من
            </NavLink>
            {isOperator && (
              <NavLink to="/manage" className={navClass}>
                مدیریت
              </NavLink>
            )}
          </nav>
          <div className="app-header__actions">
            <button
              type="button"
              className="icon-button"
              onClick={toggleTheme}
              aria-label={
                theme === "light"
                  ? "فعال‌کردن پوسته تیره"
                  : "فعال‌کردن پوسته روشن"
              }
            >
              {theme === "light" ? <Moon size={20} /> : <Sun size={20} />}
            </button>
            <NavLink className="account-link" to={user ? "/account" : "/login"}>
              {user ? <UserRound size={19} /> : <LogIn size={19} />}
              <span>{user ? user.display_name : "ورود"}</span>
            </NavLink>
          </div>
        </div>
      </header>

      <main id="main-content" className="app-main">
        <Outlet />
      </main>

      <nav className="bottom-nav" aria-label="ناوبری تلفن همراه">
        <NavLink to="/" end className={navClass}>
          <BusFront size={21} />
          <span>سفرها</span>
        </NavLink>
        <NavLink to="/bookings" className={navClass}>
          <ClipboardList size={21} />
          <span>رزروهای من</span>
        </NavLink>
        {isOperator && (
          <NavLink to="/manage" className={navClass}>
            <Settings size={21} />
            <span>مدیریت</span>
          </NavLink>
        )}
        <NavLink to={user ? "/account" : "/login"} className={navClass}>
          {user ? <UserRound size={21} /> : <LogIn size={21} />}
          <span>{user ? "حساب من" : "ورود"}</span>
        </NavLink>
      </nav>
    </div>
  );
}
