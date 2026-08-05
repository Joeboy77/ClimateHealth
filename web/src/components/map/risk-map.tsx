"use client";

import { useEffect, useMemo, useState } from "react";

import { WeatherField } from "@/components/map/weather-field";
import type { DistrictSummary, RiskLevel } from "@/lib/api/types";
import { conditionLabel, RISK_LEVELS } from "@/lib/api/types";
import {
  CLIMATE_LAYERS,
  colourFor,
  layerById,
  type ClimateLayerId,
} from "@/lib/climate-layers";
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

export function RiskMap({
  districts,
  onSelect,
  initialLayer = "risk",
  className,
}: {
  districts: readonly DistrictSummary[];
  onSelect?: (districtId: string) => void;
  initialLayer?: ClimateLayerId;
  className?: string;
}) {
  const [shapes, setShapes] = useState<Choropleth | null>(cached);
  const [hovered, setHovered] = useState<string | null>(null);
  const [layerId, setLayerId] = useState<ClimateLayerId>(initialLayer);

  useEffect(() => {
    setLayerId(initialLayer);
  }, [initialLayer]);
  const layer = layerById(layerId);

  useEffect(() => {
    let current = true;
    loadChoropleth().then((loaded) => {
      if (current) setShapes(loaded);
    });
    return () => {
      current = false;
    };
  }, []);

  const summaryById = useMemo(
    () => new Map(districts.map((district) => [district.district_id, district])),
    [districts],
  );

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

  const active = hovered ? summaryById.get(hovered) : null;
  const { width, height } = shapes.viewBox;

  return (
    <div className={cn("relative h-full w-full", className)}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-full w-full"
        role="img"
        aria-label={`Risk map of Ghana. ${districts.length} districts coloured by current risk level.`}
        onMouseLeave={() => setHovered(null)}
      >
        <g>
          {shapes.districts.map((shape) => {
            const summary = summaryById.get(shape.id);
            const level = summary?.overall_risk_level;
            const isHovered = hovered === shape.id;
            return (
              <path
                key={shape.id}
                d={shape.d}
                fill={
                  layerId === "risk"
                    ? level
                      ? RISK_CSS_VARIABLE[level]
                      : "var(--color-raised)"
                    : colourFor(layer, summary ? layer.read(summary) : null)
                }
                fillOpacity={level ? (isHovered ? 1 : 0.82) : 0.5}
                stroke="var(--color-canvas)"
                strokeWidth={isHovered ? 1.4 : 0.4}
                onMouseEnter={() => setHovered(shape.id)}
                onClick={() => summary && onSelect?.(shape.id)}
                className={cn(
                  "transition-[fill-opacity,stroke-width] duration-[var(--duration-instant)]",
                  summary && onSelect && "cursor-pointer",
                )}
              />
            );
          })}
        </g>

        <WeatherField
          districts={districts}
          layer={layer}
          projection={shapes.projection}
        />

        <g className="pointer-events-none">
          {shapes.regions.map((region) => (
            <path
              key={region.name}
              d={region.d}
              fill="none"
              stroke="var(--color-canvas)"
              strokeWidth={1.4}
              strokeOpacity={0.8}
              strokeLinejoin="round"
            />
          ))}
        </g>
      </svg>

      {active ? (
        <div className="pointer-events-none absolute right-3 top-3 max-w-[15rem] rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 shadow-[var(--shadow-2)]">
          <p className="text-h3">{active.name}</p>
          <p className="mt-0.5 text-[0.75rem] text-[var(--color-muted)]">
            {active.region}
          </p>
          <p className="mt-1.5 flex items-center gap-1.5 text-[0.75rem]">
            <span
              aria-hidden
              className="size-2 rounded-full"
              style={{
                backgroundColor: RISK_CSS_VARIABLE[active.overall_risk_level],
              }}
            />
            <span className="capitalize">{active.overall_risk_level}</span>
            {active.leading_condition ? (
              <span className="text-[var(--color-muted)]">
                · {conditionLabel(active.leading_condition)}
              </span>
            ) : null}
          </p>
          {layerId !== "risk"
            ? (() => {
                const reading = layer.read(active);
                return (
                  <p className="mt-1 font-mono text-[0.75rem] tabular text-[var(--color-ink)]">
                    {reading === null ? (
                      <span className="text-[var(--color-muted)]">
                        not reported
                      </span>
                    ) : (
                      <>
                        {Math.round(reading * 10) / 10}
                        <span className="text-[var(--color-muted)]">
                          {" "}
                          {layer.unit} · {layer.describe(reading)}
                        </span>
                      </>
                    )}
                  </p>
                );
              })()
            : null}
        </div>
      ) : null}

      <div className="absolute left-3 top-3 flex flex-wrap gap-1">
        {CLIMATE_LAYERS.map((option) => {
          const Icon = option.icon;
          const selected = option.id === layerId;
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => setLayerId(option.id)}
              aria-pressed={selected}
              className={cn(
                "flex items-center gap-1.5 rounded-[var(--radius-md)] border px-2 py-1 text-[0.6875rem]",
                "transition-colors duration-[var(--duration-instant)]",
                selected
                  ? "border-[var(--color-accent)]/45 bg-[var(--color-accent-subtle)] font-medium text-[var(--color-accent)]"
                  : "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-muted)] hover:border-[var(--color-border-strong)] hover:text-[var(--color-ink)]",
              )}
            >
              <Icon aria-hidden strokeWidth={2} className="size-3.5" />
              {option.label}
            </button>
          );
        })}
      </div>

      <div className="pointer-events-none absolute bottom-3 left-3 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-1.5">
        {layerId === "risk" ? (
          <div className="flex items-center gap-3">
            {RISK_LEVELS.map((level) => (
              <span key={level} className="flex items-center gap-1.5">
                <span
                  aria-hidden
                  className="size-2 rounded-full"
                  style={{
                    backgroundColor: RISK_CSS_VARIABLE[level as RiskLevel],
                  }}
                />
                <span className="text-[0.6875rem] capitalize text-[var(--color-muted)]">
                  {level}
                </span>
              </span>
            ))}
          </div>
        ) : (
          <div>
            <p className="text-[0.6875rem] text-[var(--color-muted)]">
              {layer.label} · {layer.unit}
            </p>
            <div className="mt-1 flex items-center gap-1.5">
              <span className="flex overflow-hidden rounded-[var(--radius-sm)]">
                {layer.stops.map((stop) => (
                  <span
                    key={stop.at}
                    aria-hidden
                    className="h-2 w-6"
                    style={{ backgroundColor: stop.colour }}
                  />
                ))}
              </span>
              <span className="font-mono text-[0.625rem] tabular text-[var(--color-muted)]">
                {layer.stops[0]?.at}–{layer.stops[layer.stops.length - 1]?.at}+
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
