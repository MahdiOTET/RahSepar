import { ShieldCheck, UserRound } from "lucide-react";

import {
  DEMO_ACCOUNTS,
  DEMO_PASSWORD,
  type DemoAccount,
  type DemoAccountId,
} from "./demoAccounts";

interface DemoAccountOptionsProps {
  activeAccount: DemoAccountId | null;
  disabled: boolean;
  onSelect: (account: DemoAccount) => void;
}

export function DemoAccountOptions({
  activeAccount,
  disabled,
  onSelect,
}: DemoAccountOptionsProps) {
  return (
    <aside className="demo-accounts" aria-labelledby="demo-accounts-title">
      <div className="demo-accounts__heading">
        <span className="eyebrow">ورود سریع</span>
        <h2 id="demo-accounts-title">یک حساب نمایشی انتخاب کنید</h2>
      </div>
      <div className="demo-accounts__list">
        {DEMO_ACCOUNTS.map((account) => {
          const Icon = account.id === "passenger" ? UserRound : ShieldCheck;
          const isActive = activeAccount === account.id;

          return (
            <button
              className="demo-account-option"
              type="button"
              key={account.id}
              disabled={disabled}
              onClick={() => onSelect(account)}
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
        رمز هر دو حساب <span dir="ltr">{DEMO_PASSWORD}</span> است. اطلاعات این
        محیط نمایشی و میان بازدیدکنندگان مشترک است.
      </p>
    </aside>
  );
}
