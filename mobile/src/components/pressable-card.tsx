import type { ReactNode } from "react";
import { Pressable, type ViewStyle } from "react-native";
import Animated, {
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withSpring,
  withTiming,
} from "react-native-reanimated";

import { PRESS_SCALE, duration, spring, timing } from "@/design/motion";
import { tick } from "@/design/risk";
import { MINIMUM_TARGET } from "@/design/tokens";

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

/**
 * A card that answers the thumb.
 *
 * The spring is on press and release because that is a physical interaction; under
 * Reduce Motion it falls back to an opacity change rather than to nothing, since silent
 * controls are worse for everyone than animated ones.
 */
export function PressableCard({
  children,
  onPress,
  style,
  accessibilityLabel,
  accessibilityHint,
  accessibilityState,
  disabled = false,
}: {
  children: ReactNode;
  onPress: () => void;
  style?: ViewStyle | ViewStyle[];
  accessibilityLabel: string;
  accessibilityHint?: string;
  /** Set when the card expands something, so a screen reader announces the state. */
  accessibilityState?: { expanded?: boolean; disabled?: boolean };
  disabled?: boolean;
}) {
  const pressed = useSharedValue(0);
  const reduceMotion = useReducedMotion();

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: reduceMotion ? 1 : 1 - pressed.value * (1 - PRESS_SCALE) }],
    opacity: 1 - pressed.value * (reduceMotion ? 0.25 : 0.06),
  }));

  return (
    <AnimatedPressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      accessibilityState={{ disabled, ...accessibilityState }}
      disabled={disabled}
      hitSlop={8}
      onPressIn={() => {
        pressed.value = reduceMotion
          ? withTiming(1, timing(duration.instant))
          : withSpring(1, spring.press);
        void tick();
      }}
      onPressOut={() => {
        pressed.value = reduceMotion
          ? withTiming(0, timing(duration.instant))
          : withSpring(0, spring.press);
      }}
      onPress={onPress}
      style={[{ minHeight: MINIMUM_TARGET }, style, animatedStyle]}
    >
      {children}
    </AnimatedPressable>
  );
}
