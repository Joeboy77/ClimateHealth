import {
  Buildings,
  CloudSun,
  Heartbeat,
  Leaf,
  Lifebuoy,
  type Icon as LucideIcon,
} from "@phosphor-icons/react";

import type { ActionStatus, ActionUrgency, Agency } from "./api/types";

type AgencyPresentation = {
  label: string;
  icon: LucideIcon;
  colour: string;
};

export const AGENCY_PRESENTATION: Record<Agency, AgencyPresentation> = {
  ghs: { label: "Ghana Health Service", icon: Heartbeat, colour: "#2f9c8e" },
  epa: {
    label: "Environmental Protection Agency",
    icon: Leaf,
    colour: "#5f9c3a",
  },
  gmet: {
    label: "Ghana Meteorological Agency",
    icon: CloudSun,
    colour: "#3f86c4",
  },
  nadmo: {
    label: "National Disaster Management Organisation",
    icon: Lifebuoy,
    colour: "#d4762c",
  },
  assembly: { label: "District Assembly", icon: Buildings, colour: "#8f7bc4" },
};

type StatusPresentation = { label: string; colour: string };

export const ACTION_STATUS_PRESENTATION: Record<
  ActionStatus,
  StatusPresentation
> = {
  not_started: { label: "Not started", colour: "var(--color-muted)" },
  in_progress: { label: "In progress", colour: "var(--color-accent)" },
  complete: { label: "Complete", colour: "var(--color-risk-low)" },
  blocked: { label: "Blocked", colour: "var(--color-risk-severe)" },
};

type UrgencyPresentation = {
  readonly label: string;
  readonly colour: string;
  readonly meaning: string;
};

export const ACTION_URGENCY_PRESENTATION: Record<
  ActionUrgency,
  UrgencyPresentation
> = {
  overdue: {
    label: "Overdue",
    colour: "var(--color-risk-severe)",
    meaning: "The onset window has run out and this is not closed",
  },
  stalled: {
    label: "Stalled",
    colour: "var(--color-risk-high)",
    meaning: "Nobody has touched this in 36 hours",
  },
  due_soon: {
    label: "Due soon",
    colour: "var(--color-risk-moderate)",
    meaning: "Cases are expected within a day",
  },
  on_track: {
    label: "On track",
    colour: "var(--color-muted)",
    meaning: "Inside its window",
  },
  closed: {
    label: "Closed",
    colour: "var(--color-risk-low)",
    meaning: "Completed",
  },
};

export const ESCALATED_URGENCIES: readonly ActionUrgency[] = [
  "overdue",
  "stalled",
];

export function elapsedText(hours: number): string {
  if (hours < 1) return "just now";
  if (hours < 48) return `${Math.round(hours)}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export const ACTION_STATUSES = Object.keys(
  ACTION_STATUS_PRESENTATION,
) as ActionStatus[];
