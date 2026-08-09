import {
  LogOut,
  Phone,
  ShieldCheck,
  UserRound,
  WalletCards,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../app/AuthContext";
import { formatPrice, profileLabel } from "../../lib/format";

export default function AccountPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;

  return (
    <div className="account-page page-container page-container--narrow">
      <header className="page-title">
        <span className="eyebrow">حساب من</span>
        <h1>اطلاعات شما</h1>
        <p>اطلاعات ضروری حساب و موجودی کیف پول در یک نگاه.</p>
      </header>

      <section className="profile-card">
        <div className="profile-card__identity">
          <span className="profile-card__avatar">
            <UserRound size={30} />
          </span>
          <div>
            <h2>{user.display_name}</h2>
            <span className="profile-card__roles">
              {user.profiles.map(profileLabel).join(" · ")}
            </span>
          </div>
        </div>
        <dl className="profile-details">
          <div>
            <dt>
              <Phone size={18} /> شماره موبایل
            </dt>
            <dd dir="ltr">{user.mobile}</dd>
          </div>
          <div>
            <dt>
              <WalletCards size={18} /> موجودی کیف پول
            </dt>
            <dd>{formatPrice(user.wallet_balance)}</dd>
          </div>
          <div>
            <dt>
              <ShieldCheck size={18} /> وضعیت حساب
            </dt>
            <dd>فعال</dd>
          </div>
        </dl>
        <button
          className="button button--danger-ghost"
          type="button"
          onClick={() => {
            logout();
            navigate("/", { replace: true });
          }}
        >
          <LogOut size={18} />
          خروج از حساب
        </button>
      </section>
    </div>
  );
}
