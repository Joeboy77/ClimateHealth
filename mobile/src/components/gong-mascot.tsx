import { useEffect } from "react";
import Animated, {
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withSequence,
  withSpring,
  withTiming,
} from "react-native-reanimated";

import { DawuroMark } from "./dawuro-mark";
import { colour } from "@/design/tokens";

export type MascotMood = "waiting" | "right" | "wrong" | "celebrating";

/**
 * The gong, reacting.
 *
 * Duolingo has an owl. We already have the dawuro, which is the instrument the whole
 * product is named after and is actually Ghanaian, so it does the job instead: it rings
 * when somebody is right, tilts when they are not, and swings on a finished run.
 *
 * It never looks disappointed. A character that sulks at a wrong answer is a small
 * cruelty aimed at somebody who is trying to learn how to keep their family well.
 */
export function GongMascot({ mood, size = 72 }: { mood: MascotMood; size?: number }) {
  const reduceMotion = useReducedMotion();
  const swing = useSharedValue(0);
  const lift = useSharedValue(0);

  useEffect(() => {
    if (reduceMotion) return;

    if (mood === "right") {
      swing.value = withSequence(
        withTiming(-12, { duration: 90 }),
        withSpring(0, { damping: 6, stiffness: 260 }),
      );
      lift.value = withSequence(
        withSpring(1, { damping: 9, stiffness: 320 }),
        withSpring(0, { damping: 12, stiffness: 220 }),
      );
      return;
    }

    if (mood === "wrong") {
      // A slow tilt, not a shake. Nobody is being told off.
      swing.value = withSequence(
        withTiming(7, { duration: 220 }),
        withTiming(0, { duration: 320 }),
      );
      return;
    }

    if (mood === "celebrating") {
      swing.value = withSequence(
        withTiming(-16, { duration: 140 }),
        withSpring(0, { damping: 4, stiffness: 180 }),
      );
      lift.value = withSequence(
        withSpring(1.4, { damping: 7, stiffness: 260 }),
        withSpring(0, { damping: 10, stiffness: 200 }),
      );
    }
  }, [mood, reduceMotion, swing, lift]);

  const style = useAnimatedStyle(() => ({
    transform: [
      { translateY: -lift.value * 10 },
      { rotate: `${swing.value}deg` },
      { scale: 1 + lift.value * 0.06 },
    ],
  }));

  const tint =
    mood === "wrong"
      ? colour.riskModerate
      : mood === "waiting"
        ? colour.inkFaint
        : colour.accent;

  return (
    <Animated.View
      style={style}
      accessibilityElementsHidden
      importantForAccessibility="no"
    >
      <DawuroMark colour={tint} size={size} />
    </Animated.View>
  );
}
