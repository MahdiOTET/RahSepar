import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { IranRouteMap } from "./IranRouteMap";

describe("IranRouteMap", () => {
  it("shows a geographic route for supported Iranian cities", () => {
    const { container } = render(
      <IranRouteMap origin="اصفهان" destination="تهران" />,
    );

    expect(
      screen.getByRole("img", { name: "نقشه مسیر از اصفهان به تهران" }),
    ).toBeInTheDocument();
    expect(container.querySelector(".iran-route-map__country")).not.toBeNull();
    expect(container.querySelector(".iran-route-map__path")).not.toBeNull();
  });

  it("keeps the simple route line for an unknown city", () => {
    const { container } = render(
      <IranRouteMap origin="Unknown" destination="تهران" />,
    );

    expect(container.querySelector(".trip-card__route-line")).not.toBeNull();
    expect(container.querySelector(".iran-route-map")).toBeNull();
  });
});
