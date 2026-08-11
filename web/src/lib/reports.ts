import {
  Drop,
  Heartbeat,
  Trash,
  Waves,
  Wind,
  type Icon as LucideIcon,
} from "@phosphor-icons/react";

import type { ReportType } from "./api/types";

type ReportPresentation = {
  label: string;
  icon: LucideIcon;
  hint: string;
};

export const REPORT_PRESENTATION: Record<ReportType, ReportPresentation> = {
  stagnant_water: {
    label: "Stagnant water",
    icon: Drop,
    hint: "Standing water that could breed mosquitoes",
  },
  flooding: {
    label: "Flooding",
    icon: Waves,
    hint: "Water covering ground, homes or roads",
  },
  unsafe_water: {
    label: "Unsafe water",
    icon: Drop,
    hint: "A drinking water source that looks or tastes wrong",
  },
  illness_cluster: {
    label: "Illness cluster",
    icon: Heartbeat,
    hint: "Several people unwell with similar symptoms",
  },
  waste_dumping: {
    label: "Waste dumping",
    icon: Trash,
    hint: "Refuse blocking drains or piling up",
  },
  dust_haze: {
    label: "Dust haze",
    icon: Wind,
    hint: "Heavy dust in the air",
  },
};

export const REPORT_TYPES = Object.keys(REPORT_PRESENTATION) as ReportType[];

export function reportPresentation(type: ReportType): ReportPresentation {
  return REPORT_PRESENTATION[type];
}

export function formatCoordinates(
  latitude: number | null,
  longitude: number | null,
): string | null {
  if (latitude === null || longitude === null) return null;
  const northSouth = latitude >= 0 ? "N" : "S";
  const eastWest = longitude >= 0 ? "E" : "W";
  return `${Math.abs(latitude).toFixed(4)}° ${northSouth}, ${Math.abs(longitude).toFixed(4)}° ${eastWest}`;
}
