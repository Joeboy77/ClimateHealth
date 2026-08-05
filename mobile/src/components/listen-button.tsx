import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Svg, { Path, Rect } from "react-native-svg";

import { tick } from "@/design/risk";
import { MINIMUM_TARGET, colour, family, radius, space, type } from "@/design/tokens";
import type { NarrationLanguage } from "@/lib/api/types";
import { canSpeak, speak, stop, type Speakable } from "@/lib/speech/speak";

/**
 * Listen.
 *
 * Prominent for a Voice-First Guardian and quieter for everybody else, because the tier
 * is named for this and the rest of us mostly read. It stops as readily as it starts: an
 * audio control you cannot interrupt is worse than none on a shared phone.
 *
 * If the phone has no voice for the language the text is in, it says so rather than
 * reading Twi in an English voice.
 */
export function ListenButton({
  parts,
  language,
  prominent = false,
}: {
  parts: readonly Speakable[];
  language: NarrationLanguage;
  prominent?: boolean;
}) {
  const [speaking, setSpeaking] = useState(false);
  const [available, setAvailable] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    void canSpeak(language).then((can) => {
      if (!cancelled) setAvailable(can);
    });
    return () => {
      cancelled = true;
      void stop();
    };
  }, [language]);

  if (available === false) {
    return (
      <Text style={styles.unavailable}>
        This phone cannot read {languageName(language)} aloud yet.
      </Text>
    );
  }

  const toggle = () => {
    void tick();
    if (speaking) {
      void stop();
      setSpeaking(false);
      return;
    }
    setSpeaking(true);
    void speak(parts, () => setSpeaking(false));
  };

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={speaking ? "Stop reading aloud" : "Read this aloud"}
      accessibilityState={{ busy: speaking }}
      onPress={toggle}
      style={[styles.button, prominent && styles.prominent]}
    >
      <View style={styles.icon}>{speaking ? <StopMark /> : <PlayMark />}</View>
      <Text style={[styles.label, prominent && styles.labelProminent]}>
        {speaking ? "Stop" : "Listen"}
      </Text>
    </Pressable>
  );
}

function languageName(language: NarrationLanguage): string {
  const names: Record<string, string> = {
    en: "English",
    tw: "Twi",
    gaa: "Ga",
    ee: "Ewe",
    dag: "Dagbani",
  };
  return names[language] ?? "this language";
}

function PlayMark() {
  return (
    <Svg width={16} height={16} viewBox="0 0 24 24">
      <Path d="M8 5.5v13l11-6.5z" fill={colour.accent} />
    </Svg>
  );
}

function StopMark() {
  return (
    <Svg width={16} height={16} viewBox="0 0 24 24">
      <Rect x={6} y={6} width={12} height={12} rx={2} fill={colour.accent} />
    </Svg>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: MINIMUM_TARGET,
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: space.snug,
    borderWidth: 1.5,
    borderColor: colour.accent,
    borderRadius: radius.pill,
    paddingHorizontal: space.comfortable,
  },
  prominent: {
    alignSelf: "stretch",
    justifyContent: "center",
    minHeight: MINIMUM_TARGET + 12,
    backgroundColor: colour.accentSubtle,
  },
  icon: { width: 16, height: 16 },
  label: {
    ...type.body,
    fontFamily: family.bodySemibold,
    color: colour.accent,
  },
  labelProminent: { ...type.heading, fontFamily: family.bodySemibold },
  unavailable: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.inkFaint,
  },
});
