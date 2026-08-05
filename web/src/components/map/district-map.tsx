"use client";

import { useEffect, useState } from "react";

import type { CommunityReport, RiskLevel } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { RISK_CSS_VARIABLE } from "@/lib/risk";

type DistrictMapEntry = {
  shapeName: string;
  viewBox: { width: number; height: number };
  projection: { scale: number; translateX: number; translateY: number };
  bounds: { west: number; south: number; east: number; north: number };
  d: string;
};

const geometryCache = new Map<string, DistrictMapEntry>();

async function loadGeometry(districtId: string): Promise<DistrictMapEntry | null> {
  const cached = geometryCache.get(districtId);
  if (cached) return cached;
  const response = await fetch(`/district-maps/${districtId}.json`);
  if (!response.ok) return null;
  const entry = (await response.json()) as DistrictMapEntry;
  geometryCache.set(districtId, entry);
  return entry;
}

const REPORT_TYPE_LABELS: Record<string, string> = {
  stagnant_water: "Stagnant water",
  flooding: "Flooding",
  unsafe_water: "Unsafe water",
  illness_cluster: "Illness cluster",
  waste_dumping: "Waste dumping",
  dust_haze: "Dust haze",
};

function project(
  entry: DistrictMapEntry,
  longitude: number,
  latitude: number,
): { x: number; y: number } {
  const { scale, translateX, translateY } = entry.projection;
  return {
    x: scale * ((longitude * Math.PI) / 180) + translateX,
    y:
      translateY -
      scale * Math.log(Math.tan(Math.PI / 4 + (latitude * Math.PI) / 360)),
  };
}

function withinBounds(
  entry: DistrictMapEntry,
  longitude: number,
  latitude: number,
): boolean {
  const { west, south, east, north } = entry.bounds;
  return (
    longitude >= west && longitude <= east && latitude >= south && latitude <= north
  );
}

const PIN_SEPARATION = 22;

type Pin = { report: CommunityReport; x: number; y: number };

/**
 * Reports cluster within a few hundred metres of each other, which is a few
 * pixels at district zoom. Fan overlapping pins around their shared point and
 * keep a leader back to the true location.
 */
function spread(pins: Pin[]): (Pin & { anchorX: number; anchorY: number })[] {
  return pins.map((pin) => {
    const overlapping = pins.filter(
      (other) => Math.hypot(other.x - pin.x, other.y - pin.y) < PIN_SEPARATION,
    );
    if (overlapping.length < 2) {
      return { ...pin, anchorX: pin.x, anchorY: pin.y };
    }
    const position = overlapping.findIndex(
      (other) => other.report.report_id === pin.report.report_id,
    );
    const angle = (position / overlapping.length) * Math.PI * 2 - Math.PI / 2;
    return {
      ...pin,
      anchorX: pin.x,
      anchorY: pin.y,
      x: pin.x + Math.cos(angle) * PIN_SEPARATION,
      y: pin.y + Math.sin(angle) * PIN_SEPARATION,
    };
  });
}

export function DistrictMap({
  districtId,
  districtName,
  level,
  centre,
  reports,
  className,
}: {
  districtId: string;
  districtName: string;
  level: RiskLevel;
  centre: { latitude: number; longitude: number };
  reports: readonly CommunityReport[];
  className?: string;
}) {
  const [entry, setEntry] = useState<DistrictMapEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState<string | null>(null);

  useEffect(() => {
    let current = true;
    setLoading(true);
    loadGeometry(districtId).then((loaded) => {
      if (!current) return;
      setEntry(loaded);
      setLoading(false);
    });
    return () => {
      current = false;
    };
  }, [districtId]);

  if (loading) {
    return (
      <div className={cn("h-full w-full", className)}>
        <div className="h-full w-full animate-pulse rounded-[var(--radius-md)] bg-[var(--color-raised)]" />
      </div>
    );
  }

  if (!entry) {
    return (
      <div
        className={cn(
          "grid place-items-center rounded-[var(--radius-md)] border border-dashed border-[var(--color-border)] p-6",
          className,
        )}
      >
        <p className="text-small text-[var(--color-muted)]">
          No boundary published for this district.
        </p>
      </div>
    );
  }

  const colour = RISK_CSS_VARIABLE[level];
  const { width, height } = entry.viewBox;
  const centrePoint = project(entry, centre.longitude, centre.latitude);

  const pins = spread(
    reports
      .filter(
        (report) =>
          report.latitude !== null &&
          report.longitude !== null &&
          withinBounds(entry, report.longitude, report.latitude),
      )
      .map((report) => ({
        report,
        ...project(entry, report.longitude as number, report.latitude as number),
      })),
  );

  return (
    <div className={cn("relative", className)}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-full w-full"
        role="img"
        aria-label={`Map of ${districtName} showing ${pins.length} community reports`}
      >
        <path
          d={entry.d}
          fill={colour}
          fillOpacity={0.14}
          stroke={colour}
          strokeWidth={1.6}
          strokeLinejoin="round"
        />

        <circle
          cx={centrePoint.x}
          cy={centrePoint.y}
          r={6}
          fill={colour}
          stroke="var(--color-surface)"
          strokeWidth={2}
        />
        <text
          x={centrePoint.x}
          y={centrePoint.y - 34}
          textAnchor="middle"
          className="fill-[var(--color-ink)] text-[12px] font-semibold"
        >
          {districtName}
        </text>

        {pins.map(({ report, x, y, anchorX, anchorY }) => {
          const isActive = active === report.report_id;
          const fanned = anchorX !== x || anchorY !== y;
          return (
            <g
              key={report.report_id}
              onMouseEnter={() => setActive(report.report_id)}
              onMouseLeave={() => setActive(null)}
              className="cursor-default"
            >
              {fanned ? (
                <line
                  x1={anchorX}
                  y1={anchorY}
                  x2={x}
                  y2={y}
                  stroke="var(--color-accent)"
                  strokeWidth={1}
                  strokeOpacity={0.5}
                />
              ) : null}
              <circle
                cx={x}
                cy={y}
                r={isActive ? 7 : 5}
                fill="var(--color-surface)"
                stroke="var(--color-accent)"
                strokeWidth={2}
                className="transition-all duration-[var(--duration-instant)]"
              />
              <circle cx={x} cy={y} r={1.8} fill="var(--color-accent)" />
              <title>
                {REPORT_TYPE_LABELS[report.report_type] ?? report.report_type} —{" "}
                {report.note}
              </title>
            </g>
          );
        })}
      </svg>

      <div className="pointer-events-none absolute bottom-2 left-2 flex items-center gap-3 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-1.5">
        <span className="flex items-center gap-1.5">
          <span
            aria-hidden
            className="size-2 rounded-full"
            style={{ backgroundColor: colour }}
          />
          <span className="text-[0.6875rem] text-[var(--color-muted)]">
            District centre
          </span>
        </span>
        <span className="flex items-center gap-1.5">
          <span
            aria-hidden
            className="size-2 rounded-full border-2 border-[var(--color-accent)]"
          />
          <span className="text-[0.6875rem] text-[var(--color-muted)]">
            Community report ({pins.length})
          </span>
        </span>
      </div>
    </div>
  );
}
