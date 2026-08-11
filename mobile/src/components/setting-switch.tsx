import { Pressable, StyleSheet, Switch, Text, View } from "react-native";

import { tick } from "@/design/risk";
import { MINIMUM_TARGET, colour, family, radius, space, type } from "@/design/tokens";

/** A labelled switch with the explanation underneath, because a toggle whose effect
 *  is not stated is a toggle nobody touches. The whole row is the target. */
export function SettingSwitch({
  label,
  description,
  value,
  onChange,
}: {
  label: string;
  description: string;
  value: boolean;
  onChange: (next: boolean) => void;
}) {
  const toggle = () => {
    void tick();
    onChange(!value);
  };

  return (
    <Pressable
      onPress={toggle}
      accessibilityRole="switch"
      accessibilityState={{ checked: value }}
      accessibilityLabel={label}
      accessibilityHint={description}
      style={styles.row}
    >
      <View style={styles.text}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.description}>{description}</Text>
      </View>
      <Switch
        value={value}
        onValueChange={toggle}
        trackColor={{ false: colour.border, true: colour.accent }}
        thumbColor={colour.canvas}
      />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    minHeight: MINIMUM_TARGET,
    flexDirection: "row",
    alignItems: "center",
    gap: space.comfortable,
    paddingVertical: space.snug,
    paddingHorizontal: space.comfortable,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colour.border,
    marginTop: space.snug,
  },
  text: { flex: 1, gap: 2 },
  label: { ...type.body, fontFamily: family.bodySemibold, color: colour.ink },
  description: { ...type.caption, color: colour.inkMuted },
});
