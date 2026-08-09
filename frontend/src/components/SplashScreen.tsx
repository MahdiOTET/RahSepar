import { useEffect } from "react";
import { ArrowLeft, ExternalLink } from "lucide-react";

import { BrandMark } from "./BrandMark";
import { preloadHome } from "../lib/catalog";

const SPLASH_SEEN_KEY = "rahsepar.splash-seen";
const SPLASH_DURATION_MS = 5_000;
const DEFAULT_RELEASE_URL =
  "https://github.com/MahdiOTET/RahSepar/releases/tag/v1.0.0";

export function hasSeenSplash(): boolean {
  return sessionStorage.getItem(SPLASH_SEEN_KEY) === "true";
}

interface SplashScreenProps {
  onComplete: () => void;
}

export function SplashScreen({ onComplete }: SplashScreenProps) {
  useEffect(() => {
    void preloadHome().catch(() => undefined);
    const timer = window.setTimeout(() => {
      sessionStorage.setItem(SPLASH_SEEN_KEY, "true");
      onComplete();
    }, SPLASH_DURATION_MS);
    return () => window.clearTimeout(timer);
  }, [onComplete]);

  const skip = () => {
    sessionStorage.setItem(SPLASH_SEEN_KEY, "true");
    onComplete();
  };
  const releaseUrl =
    import.meta.env.VITE_CLI_RELEASE_URL || DEFAULT_RELEASE_URL;

  return (
    <section className="splash" aria-label="راه‌اندازی راه‌سپار">
      <div className="splash__route" aria-hidden="true">
        <span className="splash__route-line" />
        <span className="splash__route-dot splash__route-dot--start" />
        <span className="splash__route-dot splash__route-dot--end" />
      </div>
      <div className="splash__content">
        <BrandMark inverse />
        <p className="splash__eyebrow">ساده‌تر از همیشه سفر کنید</p>
        <h1>جست‌وجو و رزرو سفرهای بین‌شهری ایران</h1>
        <div
          className="splash__progress"
          role="progressbar"
          aria-label="در حال آماده‌سازی برنامه"
        >
          <span />
        </div>
        <p className="splash__credit" dir="ltr">
          Developed by MahdiOTET
        </p>
        <a
          className="splash__cli-link"
          href={releaseUrl}
          target="_blank"
          rel="noreferrer"
        >
          نسخه خط فرمان
          <ExternalLink size={16} aria-hidden="true" />
        </a>
      </div>
      <button className="splash__skip" type="button" onClick={skip}>
        ورود به برنامه
        <ArrowLeft size={18} aria-hidden="true" />
      </button>
    </section>
  );
}
