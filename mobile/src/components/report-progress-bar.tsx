import { useEffect } from "react";
import { StyleSheet, Text, View } from "react-native";
import Animated, {
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";

import { colour, family, radius, space, type } from "@/design/tokens";

const STAGE_ORDER = ["submitted", "validated", "in_progress", "resolved"] as const;

/**
 * How far along somebody's report is.
 *
 * Reporting a hazard into a form that never answers is how people learn not to bother,
 * so the person who filed it sees the same stages the officers do. A rejected report
 * still shows a full bar in a muted colour: it is finished, not stalled, and saying so
 * is more honest than leaving it looking stuck forever.
 */
export function ReportProgressBar({
  stage,
  stageLabel,
  percent,
}: {
  stage: string;
  stageLabel: string;
  percent: number;
}) {
  const reduceMotion = useReducedMotion();
  const filled = useSharedValue(reduceMotion ? percent : 0);

  useEffect(() => {
    filled.value = reduceMotion ? percent : withTiming(percent, { duration: 620 });
  }, [percent, reduceMotion, filled]);

  const rejected = stage === "rejected";
  const done = stage === "resolved";
  const tint = rejected ? colour.inkFaint : done ? colour.riskLow : colour.accent;

  const fill = useAnimatedStyle(() => ({ width: `${filled.value}%` }));

  return (
    <View
      accessible
      accessibilityRole="progressbar"
      accessibilityLabel={`${stageLabel}, ${percent} per cent`}
    >
      <View style={styles.labels}>
        <Text style={[styles.stage, { color: tint }]}>{stageLabel}</Text>
        <Text style={styles.percent}>{percent}%</Text>
      </View>

      <View style={styles.track}>
        <Animated.View style={[styles.fill, { backgroundColor: tint }, fill]} />
      </View>

      {rejected ? null : (
        <View style={styles.ticks}>
          {STAGE_ORDER.map((name, index) => {
            const reached =
              index <= STAGE_ORDER.indexOf(stage as (typeof STAGE_ORDER)[number]);
            return (
              <View
                key={name}
                style={[
                  styles.tick,
                  { backgroundColor: reached ? tint : colour.border },
                ]}
              />
            );
          })}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  labels: {
    flexDirection: "row",
    alignItems: "baseline",
    justifyContent: "space-between",
    marginBottom: space.tight + 2,
  },
  stage: { ...type.caption, fontFamily: family.bodySemibold },
  percent: { ...type.caption, color: colour.inkMuted },
  track: {
    height: 8,
    borderRadius: radius.pill,
    backgroundColor: colour.raised,
    overflow: "hidden",
  },
  fill: { height: 8, borderRadius: radius.pill },
  ticks: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: space.tight + 2,
  },
  tick: { width: 6, height: 6, borderRadius: 3 },
});
