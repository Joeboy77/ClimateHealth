import {
  CloudRain,
  Drop,
  Pulse,
  Thermometer,
  Wind,
  type Icon as LucideIcon,
} from "@phosphor-icons/react";

import type { DistrictSummary } from "./api/types";

export type ClimateLayerId = "risk" | "rainfall" | "humidity" | "heat" | "dust";

export type ParticleKind = "rain" | "vapour" | "heat" | "dust" | null;

type Stop = { at: number; colour: string };

export type ClimateLayer = {
  id: ClimateLayerId;
  label: string;
  icon: LucideIcon;
  unit: string;
  particle: ParticleKind;
  /** Reading for a district, or null when the instrument reported nothing. */
  read: (district: DistrictSummary) => number | null;
  /** Ordered low-to-high colour stops. */
  stops: Stop[];
  /** Plain-language reading of a value, for the legend and tooltip. */
  describe: (value: number) => string;
};

function ramp(stops: Stop[], value: number): string {
  let chosen = stops[0]?.colour ?? "var(--color-raised)";
  for (const stop of stops) {
    if (value >= stop.at) chosen = stop.colour;
  }
  return chosen;
}

export const CLIMATE_LAYERS: ClimateLayer[] = [
  {
    id: "risk",
    label: "Health risk",
    icon: Pulse,
    unit: "",
    particle: null,
    read: () => null,
    stops: [],
    describe: () => "",
  },
  {
    id: "rainfall",
    label: "Rainfall",
    icon: CloudRain,
    unit: "mm / 7 days",
    particle: "rain",
    read: (district) => district.climate.rainfall_7d_mm,
    stops: [
      { at: 0, colour: "#1c2a33" },
      { at: 5, colour: "#20465c" },
      { at: 20, colour: "#1f6688" },
      { at: 50, colour: "#2288b0" },
      { at: 90, colour: "#3fb0d4" },
      { at: 140, colour: "#7fd6ef" },
    ],
    describe: (value) =>
      value < 5
        ? "dry week"
        : value < 20
          ? "light rain"
          : value < 50
            ? "steady rain"
            : value < 90
              ? "heavy rain"
              : "very heavy rain",
  },
  {
    id: "humidity",
    label: "Humidity",
    icon: Drop,
    unit: "% average",
    particle: "vapour",
    read: (district) => district.climate.humidity_mean_percent,
    stops: [
      { at: 0, colour: "#3d2f14" },
      { at: 25, colour: "#5c4a18" },
      { at: 45, colour: "#4c6030" },
      { at: 60, colour: "#2f7458" },
      { at: 75, colour: "#219b76" },
      { at: 88, colour: "#4fd0a4" },
    ],
    describe: (value) =>
      value < 25
        ? "very dry air"
        : value < 45
          ? "dry air"
          : value < 70
            ? "moderate"
            : value < 85
              ? "humid"
              : "saturated",
  },
  {
    id: "heat",
    label: "Peak heat",
    icon: Thermometer,
    unit: "°C daily max",
    particle: "heat",
    read: (district) => district.climate.temperature_max_c,
    stops: [
      { at: 0, colour: "#243043" },
      { at: 26, colour: "#3c5470" },
      { at: 30, colour: "#8a7440" },
      { at: 34, colour: "#c07a2c" },
      { at: 38, colour: "#d4552a" },
      { at: 41, colour: "#b32718" },
    ],
    describe: (value) =>
      value < 30
        ? "mild"
        : value < 34
          ? "warm"
          : value < 38
            ? "hot"
            : "extreme heat",
  },
  {
    id: "dust",
    label: "Dust & PM10",
    icon: Wind,
    unit: "µg/m³",
    particle: "dust",
    read: (district) =>
      district.climate.dust_concentration_ug_m3 ??
      district.climate.particulate_matter_10_ug_m3,
    stops: [
      { at: 0, colour: "#26241f" },
      { at: 10, colour: "#40392a" },
      { at: 30, colour: "#5f5335" },
      { at: 60, colour: "#8a7440" },
      { at: 100, colour: "#b3934c" },
      { at: 160, colour: "#d9bd7a" },
    ],
    describe: (value) =>
      value < 10
        ? "clear air"
        : value < 30
          ? "light haze"
          : value < 60
            ? "dusty"
            : value < 120
              ? "heavy dust"
              : "harmattan conditions",
  },
];

export function layerById(id: ClimateLayerId): ClimateLayer {
  return CLIMATE_LAYERS.find((layer) => layer.id === id) ?? CLIMATE_LAYERS[0]!;
}

export function colourFor(layer: ClimateLayer, value: number | null): string {
  if (value === null) return "var(--color-raised)";
  return ramp(layer.stops, value);
}

/**
 * Particle density for a district, 0 to 1, scaled against the layer's top stop
 * so a quiet week produces nothing and a storm produces a full field.
 */
export function intensityFor(
  layer: ClimateLayer,
  value: number | null,
): number {
  if (value === null || layer.stops.length === 0) return 0;
  const lowest = layer.stops[0]!.at;
  const highest = layer.stops[layer.stops.length - 1]!.at;
  if (highest === lowest) return 0;
  return Math.max(0, Math.min((value - lowest) / (highest - lowest), 1));
}
