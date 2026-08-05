import { useEffect } from "react";
import { View, type ViewStyle } from "react-native";
import Animated, {
  cancelAnimation,
  useAnimatedProps,
  useReducedMotion,
  useSharedValue,
  withRepeat,
  withSequence,
  withSpring,
  withTiming,
} from "react-native-reanimated";
import Svg, { Circle, G } from "react-native-svg";

import { duration, spring, timing } from "@/design/motion";
import { RISK } from "@/design/risk";
import { colour } from "@/design/tokens";
import type { RiskLevel } from "@/lib/api/types";

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

const SIZE = 220;
const STROKE = 16;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
/** Three quarters of the circle, so the gap reads as a gauge rather than a loading ring. */
const SWEEP = 0.75;
const PULSE_MS = 1800;

/**
 * The one hero moment in the app.
 *
 * The arc sweeps from zero to the level and settles with a spring, and the colour
 * interpolates through the scale rather than cutting to it, so the value reads as
 * arriving rather than as having been there all along.
 *
 * At severe the ring carries a slow, low-amplitude pulse. It is deliberately not a flash:
 * it must be noticeable in peripheral vision without being unpleasant to look at, since
 * this is the state a person most needs to sit and read.
 */
export function RiskDial({ level, style }: { level: RiskLevel; style?: ViewStyle }) {
  const progress = useSharedValue(0);
  const pulse = useSharedValue(0);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const target = RISK[level].arc;
    progress.value = reduceMotion
      ? withTiming(target, timing(duration.short))
      : withSpring(target, spring.arrive);
  }, [level, progress, reduceMotion]);

  useEffect(() => {
    if (level !== "severe" || reduceMotion) {
      cancelAnimation(pulse);
      pulse.value = withTiming(0, timing(duration.short));
      return;
    }
    pulse.value = withRepeat(
      withSequence(
        withTiming(1, timing(PULSE_MS / 2)),
        withTiming(0, timing(PULSE_MS / 2)),
      ),
      -1,
      false,
    );
    return () => cancelAnimation(pulse);
  }, [level, pulse, reduceMotion]);

  // The stroke colour is set per level rather than interpolated through an animated
  // prop. react-native-svg only reliably animates geometry across platforms, and a dial
  // whose colour disagrees with the word beside it is worse than one that changes colour
  // in a single step. The level changes about once a day, so nobody sees the step.
  const levelColour = RISK[level].colour;

  const arcProps = useAnimatedProps(() => ({
    strokeDashoffset: CIRCUMFERENCE * (1 - SWEEP * progress.value),
  }));

  const haloProps = useAnimatedProps(() => ({
    r: RADIUS + 4 + pulse.value * 7,
    opacity: pulse.value * 0.28,
  }));

  return (
    <View
      style={style}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Svg width={SIZE} height={SIZE}>
        {/* Rotated so the gauge opens at the bottom, where a thumb is not covering it. */}
        <G rotation={135} originX={SIZE / 2} originY={SIZE / 2}>
          <AnimatedCircle
            cx={SIZE / 2}
            cy={SIZE / 2}
            animatedProps={haloProps}
            stroke={levelColour}
            strokeWidth={STROKE}
            fill="none"
          />
          <Circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            stroke={colour.border}
            strokeWidth={STROKE}
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={CIRCUMFERENCE * (1 - SWEEP)}
            strokeLinecap="round"
            fill="none"
          />
          <AnimatedCircle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            animatedProps={arcProps}
            stroke={levelColour}
            strokeWidth={STROKE}
            strokeDasharray={CIRCUMFERENCE}
            strokeLinecap="round"
            fill="none"
          />
        </G>
      </Svg>
    </View>
  );
}

export const RISK_DIAL_SIZE = SIZE;
