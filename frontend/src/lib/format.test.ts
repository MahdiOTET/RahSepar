import { describe, expect, it } from "vitest";

import { formatDuration, toTehranIso } from "./format";

describe("format helpers", () => {
  it("attaches the Tehran offset to operator date-time input", () => {
    expect(toTehranIso("2026-08-10T08:30")).toBe("2026-08-10T08:30:00+03:30");
  });

  it("formats a whole-hour duration in Persian", () => {
    expect(formatDuration("2026-08-10T04:00:00Z", "2026-08-10T10:00:00Z")).toBe(
      "۶ ساعت",
    );
  });
});
