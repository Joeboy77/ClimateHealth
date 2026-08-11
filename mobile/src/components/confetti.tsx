import { useEffect } from "react";
import { StyleSheet, useWindowDimensions } from "react-native";
import Animated, {
  Easing,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withDelay,
  withTiming,
} from "react-native-reanimated";

import { colour } from "@/design/tokens";

/**
 * Confetti, hand-rolled.
 *
 * A dependency for forty falling rectangles is not worth the version risk, and rolling it
 * means the pieces can carry the app's own palette rather than arriving in somebody
 * else's primary colours.
 *
 * Under Reduce Motion nothing falls at all. Somebody who has asked the system to stop
 * things moving has asked for a reason.
 */

const PIECES = 44;
const FALL_MS = 2600;
const COLOURS = [
  colour.accent,
  colour.ochre,
  colour.riskLow,
  colour.riskModerate,
  colour.cream,
] as const;

export function Confetti({ running }: { running: boolean }) {
  const reduceMotion = useReducedMotion();
  const { width, height } = useWindowDimensions();

  if (reduceMotion || !running) return null;

  return (
    <Animated.View
      style={StyleSheet.absoluteFill}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {Array.from({ length: PIECES }, (_, index) => (
        <Piece key={index} index={index} width={width} height={height} />
      ))}
    </Animated.View>
  );
}

function Piece({
  index,
  width,
  height,
}: {
  index: number;
  width: number;
  height: number;
}) {
  const progress = useSharedValue(0);

  // Deterministic scatter from the index: a fresh Math.random on every render would
  // reshuffle the piece mid-flight.
  const startX = ((index * 97) % 100) / 100;
  const drift = (((index * 53) % 100) / 100 - 0.5) * 120;
  const spin = ((index * 31) % 6) + 2;
  const size = 6 + ((index * 17) % 7);
  const tint = COLOURS[index % COLOURS.length] ?? colour.accent;
  const delay = (index % 12) * 55;

  useEffect(() => {
    progress.value = withDelay(
      delay,
      withTiming(1, { duration: FALL_MS, easing: Easing.linear }),
    );
    // Each piece falls exactly once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const style = useAnimatedStyle(() => ({
    transform: [
      { translateY: -40 + progress.value * (height + 80) },
      { translateX: progress.value * drift },
      { rotate: `${progress.value * spin * 360}deg` },
    ],
    // Fades only in the last third, so the screen does not look like it is dissolving.
    opacity: progress.value > 0.7 ? (1 - progress.value) / 0.3 : 1,
  }));

  return (
    <Animated.View
      style={[
        {
          position: "absolute",
          left: startX * width,
          width: size,
          height: size * 1.6,
          borderRadius: 1.5,
          backgroundColor: tint,
        },
        style,
      ]}
    />
  );
}
