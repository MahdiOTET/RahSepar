interface BrandMarkProps {
  compact?: boolean;
  inverse?: boolean;
}

export function BrandMark({
  compact = false,
  inverse = false,
}: BrandMarkProps) {
  return (
    <span className={`brand-mark${compact ? " brand-mark--compact" : ""}`}>
      <svg
        className="brand-mark__symbol"
        viewBox="0 0 48 48"
        aria-hidden="true"
        focusable="false"
      >
        <path
          d="M10 35.5c8.5 0 8.4-22 19-22 4.7 0 7.7 3.2 9 7.1"
          fill="none"
          stroke={inverse ? "#50d2c8" : "currentColor"}
          strokeLinecap="round"
          strokeWidth="4"
        />
        <circle cx="10" cy="35.5" r="4.5" fill="#f4a62a" />
        <circle
          cx="38"
          cy="20.6"
          r="4.5"
          fill={inverse ? "#f7f4ed" : "#0f8c85"}
        />
      </svg>
      <span className="brand-mark__name">راه‌سپار</span>
    </span>
  );
}
