import * as Haptics from "expo-haptics";

import { colour } from "./tokens";
import type { RiskLevel } from "@/lib/api/types";

/**
 * How a risk level is presented to a citizen.
 *
 * Two rules hold this together. Colour is never the only carrier of meaning, because
 * red/green colour blindness affects roughly one man in twelve and this is a health
 * warning. And a citizen is never shown a score out of 100: a number invites false
 * precision about a person's own risk. They get a word, a window and an action.
 */

type RiskPresentation = {
  readonly label: string;
  readonly colour: string;
  readonly surface: string;
  /** Said aloud by the screen reader and shown in simplified mode. */
  readonly plain: string;
  /** Fraction of the dial arc this level fills. */
  readonly arc: number;
};

export const RISK: Record<RiskLevel, RiskPresentation> = {
  low: {
    label: "Low",
    colour: colour.riskLow,
    surface: colour.riskLowSurface,
    plain: "Risk is low today",
    arc: 0.25,
  },
  moderate: {
    label: "Moderate",
    colour: colour.riskModerate,
    surface: colour.riskModerateSurface,
    plain: "Some risk today",
    arc: 0.5,
  },
  high: {
    label: "High",
    colour: colour.riskHigh,
    surface: colour.riskHighSurface,
    plain: "Risk is high today",
    arc: 0.75,
  },
  severe: {
    label: "Severe",
    colour: colour.riskSevere,
    surface: colour.riskSevereSurface,
    plain: "Risk is very high today. Act now",
    arc: 1,
  },
};

export const RISK_ORDER: readonly RiskLevel[] = ["low", "moderate", "high", "severe"];

export function isElevated(level: RiskLevel): boolean {
  return level === "high" || level === "severe";
}

/**
 * A vibration language, consistent across the app so it can be learned by feel.
 * Proposal section 13.2: no critical information is ever carried by sound alone, and a
 * deaf or deaf-blind citizen must be able to tell an urgent warning from a routine one.
 */
export async function vibrateForLevel(level: RiskLevel): Promise<void> {
  switch (level) {
    case "severe":
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
      return;
    case "high":
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
      return;
    case "moderate":
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      return;
    case "low":
      return;
  }
}

export async function tick(): Promise<void> {
  await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
}

export async function confirm(): Promise<void> {
  await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
}

export async function reject(): Promise<void> {
  await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
}
