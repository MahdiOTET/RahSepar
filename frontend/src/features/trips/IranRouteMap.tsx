import { useId } from "react";
import { MapPin } from "lucide-react";

interface CityPoint {
  x: number;
  y: number;
}

interface IranRouteMapProps {
  origin: string;
  destination: string;
}

const CITY_POINTS: Record<string, CityPoint> = {
  تهران: { x: 37, y: 29 },
  tehran: { x: 37, y: 29 },
  مشهد: { x: 78, y: 25 },
  mashhad: { x: 78, y: 25 },
  اصفهان: { x: 38, y: 49 },
  isfahan: { x: 38, y: 49 },
  شیراز: { x: 43, y: 69 },
  shiraz: { x: 43, y: 69 },
  تبریز: { x: 12, y: 13 },
  tabriz: { x: 12, y: 13 },
  اهواز: { x: 23, y: 58 },
  ahvaz: { x: 23, y: 58 },
  رشت: { x: 28, y: 18 },
  rasht: { x: 28, y: 18 },
  کرمان: { x: 65, y: 65 },
  kerman: { x: 65, y: 65 },
  قم: { x: 34, y: 36 },
  qom: { x: 34, y: 36 },
  یزد: { x: 52, y: 54 },
  yazd: { x: 52, y: 54 },
  کرمانشاه: { x: 15, y: 38 },
  kermanshah: { x: 15, y: 38 },
  ارومیه: { x: 5, y: 16 },
  urmia: { x: 5, y: 16 },
  بندرعباس: { x: 61, y: 85 },
  "bandar abbas": { x: 61, y: 85 },
};

const IRAN_OUTLINE =
  "M 5 3 L 20 2 L 23 11 L 30 17 L 49 18 L 54 20 L 66 14 L 76 15 L 86 13 L 97 28 L 86 57 L 88 85 L 65 99 L 52 89 L 38 81 L 34 66 L 23 67 L 20 62 L 23 53 L 11 47 L 8 33 L 1 25 L 5 19 Z";

function normalizeCity(value: string): string {
  return value
    .trim()
    .toLocaleLowerCase("fa-IR")
    .replaceAll("ي", "ی")
    .replaceAll("ك", "ک");
}

export function IranRouteMap({ origin, destination }: IranRouteMapProps) {
  const markerId = `iran-route-arrow-${useId().replaceAll(":", "")}`;
  const originPoint = CITY_POINTS[normalizeCity(origin)];
  const destinationPoint = CITY_POINTS[normalizeCity(destination)];

  if (!originPoint || !destinationPoint) {
    return (
      <div className="trip-card__route-line" aria-hidden="true">
        <span />
        <span className="trip-card__route-track" />
        <MapPin size={18} />
      </div>
    );
  }

  const controlX = (originPoint.x + destinationPoint.x) / 2;
  const controlY = Math.max(
    5,
    Math.min(originPoint.y, destinationPoint.y) - 10,
  );
  const tangentX = destinationPoint.x - controlX;
  const tangentY = destinationPoint.y - controlY;
  const tangentLength = Math.hypot(tangentX, tangentY) || 1;
  const routeEndX = destinationPoint.x - (tangentX / tangentLength) * 6;
  const routeEndY = destinationPoint.y - (tangentY / tangentLength) * 6;

  return (
    <div
      className="iran-route-map"
      role="img"
      aria-label={`نقشه مسیر از ${origin} به ${destination}`}
    >
      <svg viewBox="0 0 100 100" aria-hidden="true" focusable="false">
        <defs>
          <marker
            id={markerId}
            viewBox="0 0 6 6"
            markerWidth="5"
            markerHeight="5"
            refX="5"
            refY="3"
            orient="auto"
          >
            <path className="iran-route-map__arrow" d="M 0 0 L 6 3 L 0 6 Z" />
          </marker>
        </defs>
        <path className="iran-route-map__country" d={IRAN_OUTLINE} />
        <path
          className="iran-route-map__path"
          d={`M ${originPoint.x} ${originPoint.y} Q ${controlX} ${controlY} ${routeEndX} ${routeEndY}`}
          markerEnd={`url(#${markerId})`}
        />
        <circle
          className="iran-route-map__origin-ring"
          cx={originPoint.x}
          cy={originPoint.y}
          r="4.2"
        />
        <circle
          className="iran-route-map__origin"
          cx={originPoint.x}
          cy={originPoint.y}
          r="2.1"
        />
        <rect
          className="iran-route-map__destination"
          x={destinationPoint.x - 2.8}
          y={destinationPoint.y - 2.8}
          width="5.6"
          height="5.6"
          rx="0.8"
          transform={`rotate(45 ${destinationPoint.x} ${destinationPoint.y})`}
        />
      </svg>
    </div>
  );
}
