import { StyleSheet, View } from "react-native";

import { colour, radius, space } from "@/design/tokens";

export function StepDots({ total, current }: { total: number; current: number }) {
  return (
    <View
      style={styles.dots}
      accessibilityRole="progressbar"
      accessibilityLabel={`Step ${current + 1} of ${total}`}
    >
      {Array.from({ length: total }, (_, index) => (
        <View
          key={index}
          style={[
            styles.dot,
            index === current && styles.dotCurrent,
            index < current && styles.dotDone,
          ]}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  dots: { flexDirection: "row", gap: space.snug },
  dot: {
    width: 22,
    height: 3,
    borderRadius: radius.pill,
    backgroundColor: colour.border,
  },
  dotCurrent: { backgroundColor: colour.accent },
  dotDone: { backgroundColor: colour.accent, opacity: 0.45 },
});
