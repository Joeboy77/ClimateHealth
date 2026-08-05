import type { Distinction } from "@/lib/api/types";

type DistinctionPresentation = {
  readonly label: string;
  readonly meaning: string;
  readonly cssVariable: string;
};

export const DISTINCTION: Record<Distinction, DistinctionPresentation> = {
  exemplary: {
    label: "Exemplary",
    meaning: "Nine in ten mandated actions closed before onset",
    cssVariable: "var(--color-risk-low)",
  },
  reliable: {
    label: "Reliable",
    meaning: "Seven in ten mandated actions closed before onset",
    cssVariable: "var(--color-accent)",
  },
  responding: {
    label: "Responding",
    meaning: "Actions are moving, but many close after onset",
    cssVariable: "var(--color-risk-moderate)",
  },
  unrated: {
    label: "Not yet rated",
    meaning: "Fewer than three mandated actions on record",
    cssVariable: "var(--color-muted)",
  },
};

export const AVERTED_EXPLANATION =
  "A hazard counts as averted when every mandated lead action closed before the onset window ran out. It evidences the response, not the cases that did not happen.";

export function onTimePercentage(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}
