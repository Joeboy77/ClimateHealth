"use client";

import { useEffect, useState } from "react";

import type {
  CommunityReport,
  IncidentAction,
  RiskLevel,
} from "@/lib/api/types";
import {
  AGENCY_PRESENTATION,
  ACTION_STATUS_PRESENTATION,
} from "@/lib/agencies";
import { cn } from "@/lib/cn";
import { RISK_CSS_VARIABLE } from "@/lib/risk";

type DistrictShape = {
  shapeName: string;
  viewBox: { width: number; height: number };
  projection: { scale: number; translateX: number; translateY: number };
  bounds: { west: number; south: number; east: number; north: number };
  d: string;
};

const cache = new Map<string, DistrictShape>();

async function loadShape(districtId: string): Promise<DistrictShape | null> {
  const cached = cache.get(districtId);
  if (cached) return cached;
  const response = await fetch(`/district-maps/${districtId}.json`);
  if (!response.ok) return null;
  const shape = (await response.json()) as DistrictShape;
  cache.set(districtId, shape);
  return shape;
}

function project(
  shape: DistrictShape,
  longitude: number,
  latitude: number,
): { x: number; y: number } {
  const { scale, translateX, translateY } = shape.projection;
  return {
    x: scale * ((longitude * Math.PI) / 180) + translateX,
    y:
      translateY -
      scale * Math.log(Math.tan(Math.PI / 4 + (latitude * Math.PI) / 360)),
  };
}

/** Nudge markers apart when two sit within a few pixels of each other. */
function separate<T extends { x: number; y: number }>(points: T[]): T[] {
  const placed: T[] = [];
  for (const point of points) {
    let { x, y } = point;
    let attempts = 0;
    while (
      placed.some((other) => Math.hypot(other.x - x, other.y - y) < 38) &&
      attempts < 8
    ) {
      const angle = (attempts / 8) * Math.PI * 2;
      x = point.x + Math.cos(angle) * 38;
      y = point.y + Math.sin(angle) * 38;
      attempts += 1;
    }
    placed.push({ ...point, x, y });
  }
  return placed;
}

export function OperationsMap({
  districtId,
  districtName,
  level,
  centre,
  actions,
  reports,
  highlightedActionId,
  onHighlight,
  className,
}: {
  districtId: string;
  districtName: string;
  level: RiskLevel;
  centre: { latitude: number; longitude: number };
  actions: readonly IncidentAction[];
  reports: readonly CommunityReport[];
  highlightedActionId: string | null;
  onHighlight: (actionId: string | null) => void;
  className?: string;
}) {
  const [shape, setShape] = useState<DistrictShape | null>(
    cache.get(districtId) ?? null,
  );

  useEffect(() => {
    let current = true;
    loadShape(districtId).then((loaded) => {
      if (current) setShape(loaded);
    });
    return () => {
      current = false;
    };
  }, [districtId]);

  if (!shape) {
    return (
      <div
        className={cn(
          "h-full w-full animate-pulse rounded-[var(--radius-md)] bg-[var(--color-raised)]",
          className,
        )}
      />
    );
  }

  const colour = RISK_CSS_VARIABLE[level];
  const { width, height } = shape.viewBox;
  const centrePoint = project(shape, centre.longitude, centre.latitude);

  const placedActions = separate(
    actions
      .filter((action) => action.latitude !== null && action.longitude !== null)
      .map((action) => ({
        action,
        ...project(
          shape,
          action.longitude as number,
          action.latitude as number,
        ),
      })),
  );

  const placedReports = reports
    .filter((report) => report.latitude !== null && report.longitude !== null)
    .map((report) => ({
      report,
      ...project(shape, report.longitude as number, report.latitude as number),
    }));

  return (
    <div className={cn("relative h-full w-full", className)}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-full w-full"
        role="img"
        aria-label={`Operations map of ${districtName}: ${placedActions.length} agency actions and ${placedReports.length} community reports`}
      >
        <path
          d={shape.d}
          fill={colour}
          fillOpacity={0.1}
          stroke={colour}
          strokeWidth={1.6}
          strokeLinejoin="round"
        />

        <circle
          cx={centrePoint.x}
          cy={centrePoint.y}
          r={3.5}
          fill="var(--color-muted)"
        />
        <text
          x={centrePoint.x}
          y={centrePoint.y - 10}
          textAnchor="middle"
          className="fill-[var(--color-muted)] text-[10px]"
        >
          {districtName}
        </text>

        {placedReports.map(({ report, x, y }) => (
          <g key={report.report_id}>
            <circle
              cx={x}
              cy={y}
              r={4}
              fill="none"
              stroke="var(--color-muted)"
              strokeWidth={1.5}
              strokeDasharray="2 2"
            />
            <title>Community report: {report.note}</title>
          </g>
        ))}

        {placedActions.map(({ action, x, y }) => {
          const presentation = AGENCY_PRESENTATION[action.agency];
          const statusTone = ACTION_STATUS_PRESENTATION[action.status];
          const highlighted = highlightedActionId === action.action_id;
          return (
            <g
              key={action.action_id}
              onMouseEnter={() => onHighlight(action.action_id)}
              onMouseLeave={() => onHighlight(null)}
              className="cursor-pointer"
            >
              {highlighted ? (
                <circle
                  cx={x}
                  cy={y}
                  r={19}
                  fill={presentation.colour}
                  fillOpacity={0.16}
                />
              ) : null}
              <circle
                cx={x}
                cy={y}
                r={highlighted ? 14 : 12}
                fill="var(--color-surface)"
                stroke={presentation.colour}
                strokeWidth={2}
                className="transition-all duration-[var(--duration-instant)]"
              />
              <text
                x={x}
                y={y + 3.5}
                textAnchor="middle"
                className="text-[9px] font-semibold"
                fill={presentation.colour}
              >
                {action.agency_short_name}
              </text>
              <circle
                cx={x + 9}
                cy={y - 9}
                r={3.5}
                fill={statusTone.colour}
                stroke="var(--color-surface)"
                strokeWidth={1.5}
              />
              <title>
                {action.agency_name} — {action.description} ({statusTone.label})
              </title>
            </g>
          );
        })}
      </svg>

      <div className="pointer-events-none absolute bottom-2 left-2 flex flex-wrap items-center gap-x-3 gap-y-1 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-1.5">
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
        <span className="flex items-center gap-1.5">
          <span
            aria-hidden
            className="size-2 rounded-full border border-dashed border-[var(--color-muted)]"
          />
          <span className="text-[0.6875rem] text-[var(--color-muted)]">
            Community report
          </span>
        </span>
      </div>
    </div>
  );
}
