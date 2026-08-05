"use client";

import { useEffect, useMemo, useState } from "react";

import { ACTION_STATUS_PRESENTATION } from "@/lib/agencies";
import type { DistrictSummary, IncidentAction } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { RISK_CSS_VARIABLE } from "@/lib/risk";

type Choropleth = {
  viewBox: { width: number; height: number };
  projection: { scale: number; translateX: number; translateY: number };
  districts: { id: string; d: string }[];
  regions: { name: string; d: string }[];
};

let cached: Choropleth | null = null;

async function loadChoropleth(): Promise<Choropleth | null> {
  if (cached) return cached;
  const response = await fetch("/ghana-choropleth.json");
  if (!response.ok) return null;
  cached = (await response.json()) as Choropleth;
  return cached;
}

function project(
  projection: Choropleth["projection"],
  longitude: number,
  latitude: number,
) {
  return {
    x: projection.scale * ((longitude * Math.PI) / 180) + projection.translateX,
    y:
      projection.translateY -
      projection.scale *
        Math.log(Math.tan(Math.PI / 4 + (latitude * Math.PI) / 360)),
  };
}

/**
 * Actions cluster inside a district, so at national scale they are grouped per
 * district and drawn as one pin carrying a per-status breakdown.
 */
type Cluster = {
  districtId: string;
  districtName: string;
  x: number;
  y: number;
  actions: IncidentAction[];
  agencyShortNames: string[];
};

export function NationalOperationsMap({
  actions,
  districts,
  highlightedDistrictId,
  onHighlight,
  onSelect,
  className,
}: {
  actions: readonly IncidentAction[];
  districts: readonly DistrictSummary[];
  highlightedDistrictId: string | null;
  onHighlight: (districtId: string | null) => void;
  onSelect?: (districtId: string) => void;
  className?: string;
}) {
  const [shapes, setShapes] = useState<Choropleth | null>(cached);

  useEffect(() => {
    let current = true;
    loadChoropleth().then((loaded) => {
      if (current) setShapes(loaded);
    });
    return () => {
      current = false;
    };
  }, []);

  const districtById = useMemo(
    () => new Map(districts.map((district) => [district.district_id, district])),
    [districts],
  );

  const clusters = useMemo<Cluster[]>(() => {
    if (!shapes) return [];
    const grouped = new Map<string, IncidentAction[]>();
    for (const action of actions) {
      const list = grouped.get(action.district_id) ?? [];
      list.push(action);
      grouped.set(action.district_id, list);
    }
    return [...grouped.entries()].flatMap(([districtId, list]) => {
      const district = districtById.get(districtId);
      if (!district) return [];
      return [
        {
          districtId,
          districtName: district.name,
          ...project(shapes.projection, district.longitude, district.latitude),
          actions: list,
          agencyShortNames: [
            ...new Set(list.map((action) => action.agency_short_name)),
          ],
        },
      ];
    });
  }, [actions, districtById, shapes]);

  if (!shapes) {
    return (
      <div
        className={cn(
          "h-full w-full animate-pulse rounded-[var(--radius-md)] bg-[var(--color-raised)]",
          className,
        )}
      />
    );
  }

  const activeDistrictIds = new Set(clusters.map((cluster) => cluster.districtId));
  const { width, height } = shapes.viewBox;

  return (
    <div className={cn("relative h-full w-full", className)}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-full w-full"
        role="img"
        aria-label={`National operations map: ${actions.length} actions across ${clusters.length} districts`}
      >
        {shapes.districts.map((shape) => {
          const summary = districtById.get(shape.id);
          const hasWork = activeDistrictIds.has(shape.id);
          const highlighted = highlightedDistrictId === shape.id;
          return (
            <path
              key={shape.id}
              d={shape.d}
              fill={
                hasWork && summary
                  ? RISK_CSS_VARIABLE[summary.overall_risk_level]
                  : "var(--color-raised)"
              }
              fillOpacity={hasWork ? 1 : 0.22}
              stroke={
                hasWork ? "var(--color-ink)" : "var(--color-canvas)"
              }
              strokeWidth={hasWork ? (highlighted ? 2.4 : 1.4) : 0.35}
            />
          );
        })}

        <g className="pointer-events-none">
          {shapes.regions.map((region) => (
            <path
              key={region.name}
              d={region.d}
              fill="none"
              stroke="var(--color-canvas)"
              strokeWidth={1.2}
              strokeOpacity={0.75}
              strokeLinejoin="round"
            />
          ))}
        </g>

        {clusters.map((cluster) => {
          const highlighted = highlightedDistrictId === cluster.districtId;
          const blocked = cluster.actions.some((a) => a.status === "blocked");
          return (
            <g
              key={cluster.districtId}
              onMouseEnter={() => onHighlight(cluster.districtId)}
              onMouseLeave={() => onHighlight(null)}
              onClick={() => onSelect?.(cluster.districtId)}
              className={cn(onSelect && "cursor-pointer")}
            >
              {blocked ? (
                <circle
                  cx={cluster.x}
                  cy={cluster.y}
                  r={17}
                  fill="none"
                  stroke="var(--color-risk-severe)"
                  strokeWidth={1.4}
                  className="animate-[risk-pulse_2.8s_ease-out_infinite]"
                  style={{ transformOrigin: `${cluster.x}px ${cluster.y}px` }}
                />
              ) : null}

              <circle
                cx={cluster.x}
                cy={cluster.y}
                r={highlighted ? 15 : 13}
                fill="var(--color-surface)"
                stroke="var(--color-border-strong)"
                strokeWidth={1.5}
                className="transition-all duration-[var(--duration-instant)]"
              />

              {cluster.actions.map((action, index) => {
                const slice = (index / cluster.actions.length) * Math.PI * 2;
                const radius = highlighted ? 15 : 13;
                return (
                  <circle
                    key={action.action_id}
                    cx={cluster.x + Math.cos(slice - Math.PI / 2) * radius}
                    cy={cluster.y + Math.sin(slice - Math.PI / 2) * radius}
                    r={3.2}
                    fill={ACTION_STATUS_PRESENTATION[action.status].colour}
                    stroke="var(--color-surface)"
                    strokeWidth={1.2}
                  />
                );
              })}

              <text
                x={cluster.x}
                y={cluster.y + 3.5}
                textAnchor="middle"
                className="fill-[var(--color-ink)] text-[10px] font-semibold"
              >
                {cluster.actions.length}
              </text>

              <text
                x={cluster.x}
                y={cluster.y - 21}
                textAnchor="middle"
                className="fill-[var(--color-ink)] text-[11px] font-semibold"
              >
                {cluster.districtName}
              </text>
              <text
                x={cluster.x}
                y={cluster.y + 30}
                textAnchor="middle"
                className="fill-[var(--color-muted)] text-[9.5px]"
              >
                {cluster.agencyShortNames.join(" · ")}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="pointer-events-none absolute bottom-3 left-3 flex flex-wrap items-center gap-x-3 gap-y-1 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-1.5">
        {Object.values(ACTION_STATUS_PRESENTATION).map((status) => (
          <span key={status.label} className="flex items-center gap-1.5">
            <span
              aria-hidden
              className="size-2 rounded-full"
              style={{ backgroundColor: status.colour }}
            />
            <span className="text-[0.6875rem] text-[var(--color-muted)]">
              {status.label}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
