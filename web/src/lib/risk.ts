import {
  ShieldCheck,
  Warning,
  WarningCircle,
  WarningOctagon,
  type Icon as LucideIcon,
} from "@phosphor-icons/react";

import type { ConfidenceMode, LagWindow, RiskLevel } from "./api/types";

type RiskPresentation = {
  label: string;
  icon: LucideIcon;
  foreground: string;
  surface: string;
  border: string;
  dot: string;
};

export const RISK_PRESENTATION: Record<RiskLevel, RiskPresentation> = {
  low: {
    label: "Low",
    icon: ShieldCheck,
    foreground: "text-[var(--color-risk-low)]",
    surface: "bg-[var(--color-risk-low-surface)]",
    border: "border-[var(--color-risk-low)]/25",
    dot: "bg-[var(--color-risk-low)]",
  },
  moderate: {
    label: "Moderate",
    icon: WarningCircle,
    foreground: "text-[var(--color-risk-moderate)]",
    surface: "bg-[var(--color-risk-moderate-surface)]",
    border: "border-[var(--color-risk-moderate)]/25",
    dot: "bg-[var(--color-risk-moderate)]",
  },
  high: {
    label: "High",
    icon: Warning,
    foreground: "text-[var(--color-risk-high)]",
    surface: "bg-[var(--color-risk-high-surface)]",
    border: "border-[var(--color-risk-high)]/25",
    dot: "bg-[var(--color-risk-high)]",
  },
  severe: {
    label: "Severe",
    icon: WarningOctagon,
    foreground: "text-[var(--color-risk-severe)]",
    surface: "bg-[var(--color-risk-severe-surface)]",
    border: "border-[var(--color-risk-severe)]/25",
    dot: "bg-[var(--color-risk-severe)]",
  },
};

export const RISK_CSS_VARIABLE: Record<RiskLevel, string> = {
  low: "var(--color-risk-low)",
  moderate: "var(--color-risk-moderate)",
  high: "var(--color-risk-high)",
  severe: "var(--color-risk-severe)",
};

export function riskPresentation(level: RiskLevel): RiskPresentation {
  return RISK_PRESENTATION[level];
}

/** Proposal section 6.3: the tier that produced the answer, stated openly. */
export const CONFIDENCE_COPY: Record<ConfidenceMode, string> = {
  model: "Model mode — learned model on complete signals",
  threshold: "Threshold mode — published epidemiological thresholds",
  baseline: "Baseline mode — indicative only, signals incomplete",
};

export const CONFIDENCE_SHORT: Record<ConfidenceMode, string> = {
  model: "Model",
  threshold: "Threshold",
  baseline: "Baseline",
};

export const CONFIDENCE_TIER: Record<ConfidenceMode, string> = {
  model: "Tier A",
  threshold: "Tier B",
  baseline: "Tier C",
};

const DAYS_IN_WEEK = 7;
const DAYS_IN_MONTH = 30;
const WEEK_THRESHOLD_DAYS = 21;
const MONTH_THRESHOLD_DAYS = 90;

/**
 * Days for the fast pathways. Cholera runs 2 to 10 days and rounding that to
 * "1–3 weeks" would overstate the window by enough to change a dispatch call.
 */
export function lagWindowText(window: LagWindow): string {
  const { minimum_days: minimum, maximum_days: maximum } = window;
  if (maximum <= 3) return "1–3 days";
  if (maximum >= MONTH_THRESHOLD_DAYS) {
    return `${Math.max(Math.floor(minimum / DAYS_IN_MONTH), 1)}–${Math.floor(
      maximum / DAYS_IN_MONTH,
    )} months`;
  }
  if (maximum > WEEK_THRESHOLD_DAYS) {
    return `${Math.max(Math.floor(minimum / DAYS_IN_WEEK), 1)}–${Math.floor(
      maximum / DAYS_IN_WEEK,
    )} weeks`;
  }
  if (minimum === 0) return `up to ${maximum} days`;
  return `${minimum}–${maximum} days`;
}

/** Days remaining until the earliest expected onset, for triage ordering. */
export function onsetUrgency(window: LagWindow): number {
  return window.minimum_days;
}

/**
 * The score is a normalised weight of fired triggers out of readable ones, on a
 * 0 to 100 scale. It is deliberately not called a percentage or a probability,
 * because it is neither.
 */
export function formatScore(score: number): string {
  return score.toFixed(1);
}

export const SCORE_EXPLANATION =
  "Risk score out of 100: the share of this pathway's readable trigger weight that fired. Not a probability.";

export function relativeDay(isoDate: string, today = new Date()): string {
  const observed = new Date(`${isoDate}T00:00:00`);
  const days = Math.round(
    (today.setHours(0, 0, 0, 0) - observed.getTime()) / 86_400_000,
  );
  if (days <= 0) return "today";
  if (days === 1) return "yesterday";
  return `${days} days ago`;
}
