import type { Forecast } from "@/lib/api/types";
import { persistent } from "./store";

const KEY_PREFIX = "dawuro.forecast.";

export type SavedForecast = {
  readonly forecast: Forecast;
  readonly savedAt: string;
};

/**
 * The last forecast each district showed.
 *
 * A warning that is only readable with a connection is not much of a warning. When the
 * network is gone the app shows what it last knew, dated, and says plainly that it is
 * saved rather than current. Stale information presented as fresh would be worse than
 * showing nothing; stale information that admits its age is genuinely useful.
 */

export function saveForecast(districtId: string, forecast: Forecast): void {
  persistent().set(
    `${KEY_PREFIX}${districtId}`,
    JSON.stringify({ forecast, savedAt: new Date().toISOString() }),
  );
}

export function savedForecast(districtId: string): SavedForecast | null {
  const raw = persistent().getString(`${KEY_PREFIX}${districtId}`);
  if (raw === undefined) return null;
  try {
    return JSON.parse(raw) as SavedForecast;
  } catch {
    return null;
  }
}

/** "yesterday", "3 days ago": vague on purpose, because the exact minute does not help. */
export function savedAgo(savedAt: string, now: Date = new Date()): string {
  const saved = new Date(savedAt);
  const hours = (now.getTime() - saved.getTime()) / 3_600_000;

  if (hours < 1) return "less than an hour ago";
  if (hours < 24) return `${Math.round(hours)} hours ago`;
  const days = Math.round(hours / 24);
  return days === 1 ? "yesterday" : `${days} days ago`;
}
