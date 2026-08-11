import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Animated, { FadeIn } from "react-native-reanimated";

import { Flame } from "@/components/flame";
import { duration } from "@/design/motion";
import { tick } from "@/design/risk";
import { MINIMUM_TARGET, colour, family, radius, space, type } from "@/design/tokens";

/**
 * Points and streak, at the top of the first screen.
 *
 * What somebody has built up should greet them, not be buried a tap away: it is the
 * reason to come back tomorrow. It sits above the forecast but is deliberately quieter
 * than it, because the warning is still the reason this app exists.
 *
 * A streak of zero reads as an invitation rather than a nought, since somebody who has
 * not started yet is exactly who this is trying to reach.
 */
export function GuardianBar({
  points,
  streakDays,
  levelName,
}: {
  points: number;
  streakDays: number;
  levelName: string;
}) {
  const router = useRouter();

  const streakLabel =
    streakDays > 0
      ? `${streakDays} day${streakDays === 1 ? "" : "s"} in a row`
      : "Start a streak today";

  return (
    <Animated.View entering={FadeIn.duration(duration.short)}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`${points} points, ${levelName}. ${streakLabel}. Open your Guardian card`}
        onPress={() => {
          void tick();
          router.push("/guardian");
        }}
        style={styles.bar}
      >
        <View style={styles.group}>
          <Text style={styles.points}>{points.toLocaleString()}</Text>
          <View>
            <Text style={styles.unit}>XP</Text>
            <Text style={styles.level}>{levelName}</Text>
          </View>
        </View>

        <View style={styles.divider} />

        <View style={styles.group}>
          <Flame size={18} />
          <View>
            <Text style={styles.streakDays}>{streakDays}</Text>
            <Text style={styles.level}>{streakDays === 1 ? "day" : "days"}</Text>
          </View>
        </View>
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  bar: {
    minHeight: MINIMUM_TARGET,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: space.comfortable,
    paddingVertical: space.snug,
    paddingHorizontal: space.comfortable,
    marginBottom: space.comfortable,
    borderRadius: radius.md,
    backgroundColor: colour.raised,
  },
  group: { flexDirection: "row", alignItems: "center", gap: space.snug },
  divider: { width: 1, alignSelf: "stretch", backgroundColor: colour.border },
  points: {
    ...type.title,
    fontFamily: family.display,
    color: colour.accent,
  },
  streakDays: {
    ...type.title,
    fontFamily: family.display,
    color: colour.riskModerate,
  },
  unit: { ...type.overline, color: colour.inkMuted, textTransform: "uppercase" },
  level: { ...type.caption, color: colour.inkMuted },
});
