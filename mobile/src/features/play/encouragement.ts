/**
 * What the app says back.
 *
 * Praise on a right answer, and on a wrong one something that keeps a person in the run.
 * Nothing here scolds, because the reader is somebody trying to learn how to keep their
 * household well, and a health application that makes them feel stupid has lost before it
 * has taught anything.
 */

const RIGHT = [
  "Exactly right",
  "That is it",
  "Well spotted",
  "Correct",
  "You have it",
  "Sharp",
] as const;

const WRONG = [
  "Not this time. Here is why",
  "Close. This is the one",
  "Good try. Read this bit",
  "Not quite, and this is the reason",
] as const;

const FINISH_PERFECT = [
  "Every single one. Your district is safer for it.",
  "A clean run. You know this hazard well.",
] as const;

const FINISH_STRONG = [
  "Strong run. Come back tomorrow and keep it going.",
  "Well done. That knowledge is worth having before the rain.",
] as const;

const FINISH_LEARNING = [
  "You learned something today, which is the whole point.",
  "Every answer taught you something. That counts.",
] as const;

function pick<T>(list: readonly T[], seed: number): T {
  const chosen = list[Math.abs(seed) % list.length];
  // The lists are never empty, but the type says they could be.
  return chosen ?? list[0]!;
}

export function verdictLine(correct: boolean, seed: number): string {
  return correct ? pick(RIGHT, seed) : pick(WRONG, seed);
}

export function finishLine(correct: number, total: number, seed: number): string {
  if (total > 0 && correct === total) return pick(FINISH_PERFECT, seed);
  if (correct >= Math.ceil(total * 0.6)) return pick(FINISH_STRONG, seed);
  return pick(FINISH_LEARNING, seed);
}

/** Out of five stars, so a run always reads as progress rather than a pass or a fail. */
export function starsFor(correct: number, total: number): number {
  if (total <= 0) return 0;
  return Math.max(1, Math.round((correct / total) * 5));
}
