import {
  Easing,
  ReduceMotion,
  type WithSpringConfig,
  type WithTimingConfig,
} from "react-native-reanimated";

/**
 * Motion constants.
 *
 * The rule this file exists to enforce: motion explains a change that already happened,
 * or gives feedback for a gesture. It never decorates and never delays somebody trying
 * to read a warning. Every value here is deliberately short.
 */

export const duration = {
  /** Press feedback. Below this a change reads as a glitch. */
  instant: 90,
  /** Most state changes: colour, opacity, small position shifts. */
  short: 170,
  /** A change worth noticing: the verdict word swapping over. */
  medium: 260,
  /** The one long one: the risk dial sweeping to its value on first read. */
  reveal: 620,
} as const;

/** Decelerating. Things arriving on screen. */
export const easeOut = Easing.bezier(0.2, 0, 0.38, 0.9);
/** Symmetric. Things changing in place. */
export const easeInOut = Easing.bezier(0.4, 0, 0.2, 1);

export const timing = (
  durationMs: number = duration.short,
  easing = easeOut,
): WithTimingConfig => ({
  duration: durationMs,
  easing,
  reduceMotion: ReduceMotion.System,
});

/**
 * Springs are for things a finger is touching or has just let go of. Physical motion for
 * physical interaction; curves for everything else.
 */
export const spring = {
  /** Press and release. Tight, no visible overshoot. */
  press: {
    damping: 26,
    stiffness: 420,
    mass: 0.7,
    reduceMotion: ReduceMotion.System,
  } satisfies WithSpringConfig,

  /** A sheet or card settling after a drag. */
  settle: {
    damping: 22,
    stiffness: 210,
    mass: 0.9,
    reduceMotion: ReduceMotion.System,
  } satisfies WithSpringConfig,

  /** The dial arriving at its value. Slower, with a trace of overshoot so it feels landed. */
  arrive: {
    damping: 17,
    stiffness: 120,
    mass: 1,
    reduceMotion: ReduceMotion.System,
  } satisfies WithSpringConfig,
} as const;

/** How far a pressable travels down under a thumb. Small: this is feedback, not a game. */
export const PRESS_SCALE = 0.97;

/**
 * First-mount stagger for a list. Capped, because staggering a long list means the last
 * item arrives after the reader has already looked at it.
 */
export const STAGGER_STEP_MS = 45;
export const STAGGER_MAXIMUM_ITEMS = 6;

export function staggerDelay(index: number): number {
  return Math.min(index, STAGGER_MAXIMUM_ITEMS) * STAGGER_STEP_MS;
}
