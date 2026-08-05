import { Pressable, StyleSheet, Text, View } from "react-native";
import Animated, {
  useAnimatedStyle,
  useDerivedValue,
  useReducedMotion,
  withSpring,
  withTiming,
} from "react-native-reanimated";

import { duration, spring, timing } from "@/design/motion";
import { tick } from "@/design/risk";
import { MINIMUM_TARGET, colour, family, radius, space, type } from "@/design/tokens";

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

/**
 * A single choice in a list of them.
 *
 * Selection is carried by three things at once: the fill, the border, and a mark. Colour
 * alone would fail the one man in twelve with red/green colour blindness, and this is the
 * screen where somebody tells us how old they are, which decides what the app shows a
 * child for the next year.
 */
export function Choice({
  label,
  detail,
  selected,
  onSelect,
  accessibilityHint,
}: {
  label: string;
  detail?: string;
  selected: boolean;
  onSelect: () => void;
  accessibilityHint?: string;
}) {
  const reduceMotion = useReducedMotion();
  const chosen = useDerivedValue(() =>
    reduceMotion
      ? withTiming(selected ? 1 : 0, timing(duration.instant))
      : withSpring(selected ? 1 : 0, spring.press),
  );

  const containerStyle = useAnimatedStyle(() => ({
    borderColor: chosen.value > 0.5 ? colour.accent : colour.border,
    backgroundColor: chosen.value > 0.5 ? colour.accentSubtle : colour.surface,
    transform: [{ scale: 1 + chosen.value * 0.012 }],
  }));

  const markStyle = useAnimatedStyle(() => ({
    opacity: chosen.value,
    transform: [{ scale: 0.4 + chosen.value * 0.6 }],
  }));

  return (
    <AnimatedPressable
      accessibilityRole="radio"
      accessibilityState={{ selected }}
      accessibilityLabel={detail ? `${label}. ${detail}` : label}
      accessibilityHint={accessibilityHint}
      onPress={() => {
        void tick();
        onSelect();
      }}
      style={[styles.container, containerStyle]}
    >
      <View style={styles.text}>
        <Text style={[styles.label, selected && styles.labelSelected]}>{label}</Text>
        {detail ? <Text style={styles.detail}>{detail}</Text> : null}
      </View>
      <View style={[styles.ring, selected && styles.ringSelected]}>
        <Animated.View style={[styles.mark, markStyle]} />
      </View>
    </AnimatedPressable>
  );
}

const styles = StyleSheet.create({
  container: {
    minHeight: MINIMUM_TARGET + 8,
    flexDirection: "row",
    alignItems: "center",
    gap: space.base,
    borderWidth: 1.5,
    borderRadius: radius.md,
    paddingVertical: space.base,
    paddingHorizontal: space.comfortable,
    marginBottom: space.snug,
  },
  text: { flex: 1 },
  label: {
    ...type.body,
    fontFamily: family.bodyMedium,
    color: colour.ink,
  },
  labelSelected: { color: colour.accentPressed },
  detail: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: 2,
  },
  ring: {
    width: 22,
    height: 22,
    borderRadius: radius.pill,
    borderWidth: 1.5,
    borderColor: colour.borderStrong,
    alignItems: "center",
    justifyContent: "center",
  },
  ringSelected: { borderColor: colour.accent },
  mark: {
    width: 11,
    height: 11,
    borderRadius: radius.pill,
    backgroundColor: colour.accent,
  },
});
