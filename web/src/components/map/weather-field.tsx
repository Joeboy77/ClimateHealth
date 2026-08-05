"use client";

import { useMemo, type CSSProperties } from "react";

import type { DistrictSummary } from "@/lib/api/types";
import {
  intensityFor,
  type ClimateLayer,
  type ParticleKind,
} from "@/lib/climate-layers";

const MAX_PARTICLES = 190;
const PARTICLES_PER_DISTRICT = 4;

type Projection = { scale: number; translateX: number; translateY: number };

type Particle = {
  key: string;
  x: number;
  y: number;
  delay: number;
  duration: number;
  size: number;
};

function project(
  projection: Projection,
  longitude: number,
  latitude: number,
): { x: number; y: number } {
  return {
    x: projection.scale * ((longitude * Math.PI) / 180) + projection.translateX,
    y:
      projection.translateY -
      projection.scale *
        Math.log(Math.tan(Math.PI / 4 + (latitude * Math.PI) / 360)),
  };
}

/** Deterministic jitter so particles do not leap about on every re-render. */
function scatter(seed: number): number {
  const value = Math.sin(seed * 12.9898) * 43758.5453;
  return value - Math.floor(value);
}

function buildParticles(
  districts: readonly DistrictSummary[],
  layer: ClimateLayer,
  projection: Projection,
): Particle[] {
  const ranked = districts
    .map((district) => ({
      district,
      intensity: intensityFor(layer, layer.read(district)),
    }))
    .filter((entry) => entry.intensity > 0.12)
    .sort((first, second) => second.intensity - first.intensity)
    .slice(0, Math.ceil(MAX_PARTICLES / PARTICLES_PER_DISTRICT));

  const particles: Particle[] = [];
  for (const { district, intensity } of ranked) {
    const centre = project(projection, district.longitude, district.latitude);
    const count = Math.max(1, Math.round(intensity * PARTICLES_PER_DISTRICT));
    for (let index = 0; index < count; index += 1) {
      const seed = district.district_id.length * 31 + index * 7 + centre.x;
      particles.push({
        key: `${district.district_id}-${index}`,
        x: centre.x + (scatter(seed) - 0.5) * 26,
        y: centre.y + (scatter(seed + 1) - 0.5) * 26,
        delay: scatter(seed + 2) * 2.4,
        duration: 1.5 + scatter(seed + 3) * 1.6,
        size: 0.6 + intensity * 0.9,
      });
    }
  }
  return particles;
}

export function WeatherField({
  districts,
  layer,
  projection,
}: {
  districts: readonly DistrictSummary[];
  layer: ClimateLayer;
  projection: Projection;
}) {
  const particles = useMemo(
    () => (layer.particle ? buildParticles(districts, layer, projection) : []),
    [districts, layer, projection],
  );

  const kind = layer.particle;
  if (kind === null || particles.length === 0) return null;

  return (
    <g className="pointer-events-none" aria-hidden>
      {particles.map((particle) => (
        <Particle key={particle.key} kind={kind} particle={particle} />
      ))}
    </g>
  );
}

function Particle({
  kind,
  particle,
}: {
  kind: NonNullable<ParticleKind>;
  particle: Particle;
}) {
  const style = {
    animationDelay: `${particle.delay}s`,
    ["--weather-duration" as string]: `${particle.duration}s`,
    transformOrigin: `${particle.x}px ${particle.y}px`,
    transformBox: "fill-box",
  } as CSSProperties;

  if (kind === "rain") {
    return (
      <line
        x1={particle.x}
        y1={particle.y}
        x2={particle.x - 1.4}
        y2={particle.y + 6}
        stroke="#8fd8f2"
        strokeWidth={particle.size}
        strokeLinecap="round"
        className="animate-[weather-rain_var(--weather-duration)_linear_infinite]"
        style={style}
      />
    );
  }

  if (kind === "dust") {
    return (
      <circle
        cx={particle.x}
        cy={particle.y}
        r={particle.size * 1.5}
        fill="#e0c489"
        className="animate-[weather-drift_var(--weather-duration)_ease-in-out_infinite]"
        style={style}
      />
    );
  }

  if (kind === "heat") {
    return (
      <circle
        cx={particle.x}
        cy={particle.y}
        r={particle.size * 3.4}
        fill="none"
        stroke="#f0a05a"
        strokeWidth={0.7}
        className="animate-[weather-shimmer_var(--weather-duration)_ease-out_infinite]"
        style={style}
      />
    );
  }

  return (
    <circle
      cx={particle.x}
      cy={particle.y}
      r={particle.size * 1.7}
      fill="#6fe0bb"
      className="animate-[weather-rise_var(--weather-duration)_ease-in_infinite]"
      style={style}
    />
  );
}
