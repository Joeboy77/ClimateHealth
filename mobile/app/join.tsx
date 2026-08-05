import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import Animated, { FadeIn, FadeInDown, FadeOut } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Dropdown } from "@/components/dropdown";
import { DawuroMark } from "@/components/dawuro-mark";
import { StepDots } from "@/components/field-shell";
import { WhereYouLive } from "@/features/join/where-you-live";
import { duration } from "@/design/motion";
import { confirm } from "@/design/risk";
import {
  MINIMUM_TARGET,
  colour,
  elevation,
  family,
  radius,
  space,
  type,
} from "@/design/tokens";
import { api } from "@/lib/api/client";
import { useSession } from "@/lib/identity/session";
import type { AgeBand } from "@/lib/api/types";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "tw", label: "Twi" },
  { code: "gaa", label: "Ga" },
  { code: "ee", label: "Ewe" },
  { code: "dag", label: "Dagbani" },
] as const;

const STEPS = ["name", "district", "age", "language"] as const;
type Step = (typeof STEPS)[number];

/**
 * Joining.
 *
 * Four questions, one per screen, and nothing we do not use. No password and no code sent
 * to a phone: a one-time code costs money and turns the first thirty seconds of a
 * public-health application into a chore, which is the friction that keeps the people most
 * at risk from ever arriving.
 *
 * The age band is the one question that changes the product. It decides which tier a
 * Guardian gets, whether their missions must be supervised, and whether they may be
 * offered health rewards at all. That is why it is asked plainly and why each option says
 * what it will mean.
 */
export default function JoinScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();

  const { join: keepSession } = useSession();
  const [step, setStep] = useState<Step>("name");
  const [name, setName] = useState("");
  const [districtId, setDistrictId] = useState<string | null>(null);
  const [ageBand, setAgeBand] = useState<AgeBand | null>(null);
  const [language, setLanguage] = useState<string>("en");

  const ageBands = useQuery({
    queryKey: ["age-bands"],
    queryFn: () => api.ageBands(),
  });

  const join = useMutation({
    mutationFn: () =>
      api.registerCitizen({
        display_name: name.trim(),
        district_id: districtId ?? "",
        age_band: ageBand ?? "18_34",
        language: language as "en",
      }),
    onSuccess: async (session) => {
      await keepSession(session);
      await confirm();
      router.replace("/");
    },
  });

  const index = STEPS.indexOf(step);
  const canContinue =
    (step === "name" && name.trim().length > 0) ||
    (step === "district" && districtId !== null) ||
    (step === "age" && ageBand !== null) ||
    step === "language";

  const advance = () => {
    if (step === "language") {
      join.mutate();
      return;
    }
    const next = STEPS[index + 1];
    if (next !== undefined) setStep(next);
  };

  const back = () => {
    const previous = STEPS[index - 1];
    if (previous !== undefined) setStep(previous);
  };

  return (
    <KeyboardAvoidingView
      style={styles.host}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={[styles.header, { paddingTop: insets.top + space.comfortable }]}>
        <View style={styles.headerRow}>
          <DawuroMark colour={colour.accent} size={34} />
          <StepDots total={STEPS.length} current={index} />
        </View>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        {step === "name" ? (
          <Animated.View entering={FadeIn.duration(duration.medium)} exiting={FadeOut}>
            <Text style={styles.question}>What should we call you?</Text>
            <Text style={styles.aside}>
              A first name is enough. It appears on your Guardian card and nowhere
              public.
            </Text>
            <TextInput
              value={name}
              onChangeText={setName}
              placeholder="Your name"
              placeholderTextColor={colour.inkFaint}
              autoFocus
              autoCapitalize="words"
              accessibilityLabel="Your name"
              style={styles.input}
              returnKeyType="next"
              onSubmitEditing={() => canContinue && advance()}
            />
          </Animated.View>
        ) : null}

        {step === "district" ? (
          <Animated.View entering={FadeIn.duration(duration.medium)} exiting={FadeOut}>
            <Text style={styles.question}>Where do you live?</Text>
            <Text style={styles.aside}>
              Your forecast is for your district. You can change it later.
            </Text>
            <View style={styles.list}>
              <WhereYouLive districtId={districtId} onChange={setDistrictId} />
            </View>
          </Animated.View>
        ) : null}

        {step === "age" ? (
          <Animated.View entering={FadeIn.duration(duration.medium)} exiting={FadeOut}>
            <Text style={styles.question}>How old are you?</Text>
            <Text style={styles.aside}>
              This decides what Dawuro shows you and which missions you are given. We
              ask for a range, never a birthday.
            </Text>
            <View style={styles.list}>
              <Dropdown
                label="Age range"
                placeholder="Choose your age range"
                options={(ageBands.data ?? []).map((band) => ({
                  value: band.age_band,
                  label: band.label,
                  detail: band.supervised_missions_only
                    ? `${band.tier_name} · supervised missions only`
                    : band.tier_name,
                }))}
                value={ageBand}
                onChange={(next) => setAgeBand(next as AgeBand)}
              />
            </View>
          </Animated.View>
        ) : null}

        {step === "language" ? (
          <Animated.View entering={FadeIn.duration(duration.medium)} exiting={FadeOut}>
            <Text style={styles.question}>Which language?</Text>
            <Text style={styles.aside}>
              Your daily forecast and every lesson arrive in this language.
            </Text>
            <View style={styles.list}>
              <Dropdown
                label="Language"
                placeholder="Choose your language"
                options={LANGUAGES.map((entry) => ({
                  value: entry.code,
                  label: entry.label,
                }))}
                value={language}
                onChange={setLanguage}
              />
            </View>
            {join.isError ? (
              <Text style={styles.error}>{join.error.message}</Text>
            ) : null}
          </Animated.View>
        ) : null}
      </ScrollView>

      <Animated.View
        entering={FadeInDown.duration(duration.medium)}
        style={[styles.footer, { paddingBottom: insets.bottom + space.comfortable }]}
      >
        {index > 0 ? (
          <Pressable
            onPress={back}
            accessibilityRole="button"
            accessibilityLabel="Go back"
            style={styles.back}
          >
            <Text style={styles.backText}>Back</Text>
          </Pressable>
        ) : null}
        <Pressable
          onPress={advance}
          disabled={!canContinue || join.isPending}
          accessibilityRole="button"
          accessibilityLabel={step === "language" ? "Finish and join" : "Continue"}
          accessibilityState={{ disabled: !canContinue || join.isPending }}
          style={[
            styles.primary,
            (!canContinue || join.isPending) && styles.primaryOff,
          ]}
        >
          <Text style={styles.primaryText}>
            {join.isPending
              ? "Joining…"
              : step === "language"
                ? "Become a Guardian"
                : "Continue"}
          </Text>
        </Pressable>
      </Animated.View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  host: { flex: 1, backgroundColor: colour.canvas },
  header: { paddingHorizontal: space.comfortable, paddingBottom: space.base },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  scroll: { flex: 1 },
  content: { paddingHorizontal: space.comfortable, paddingBottom: space.section },
  question: {
    ...type.display,
    fontFamily: family.display,
    color: colour.ink,
    marginTop: space.base,
  },
  aside: {
    ...type.body,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: space.base,
  },
  input: {
    ...type.title,
    fontFamily: family.bodyMedium,
    color: colour.ink,
    backgroundColor: colour.surface,
    borderWidth: 1.5,
    borderColor: colour.border,
    borderRadius: radius.md,
    paddingHorizontal: space.comfortable,
    paddingVertical: space.base,
    marginTop: space.roomy,
    minHeight: MINIMUM_TARGET + 6,
  },
  list: { marginTop: space.roomy },
  error: {
    ...type.small,
    fontFamily: family.body,
    color: colour.riskSevere,
    marginTop: space.base,
  },
  footer: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.base,
    paddingHorizontal: space.comfortable,
    paddingTop: space.base,
    borderTopWidth: 1,
    borderTopColor: colour.border,
    backgroundColor: colour.canvas,
  },
  back: {
    minHeight: MINIMUM_TARGET,
    justifyContent: "center",
    paddingHorizontal: space.comfortable,
  },
  backText: {
    ...type.body,
    fontFamily: family.bodyMedium,
    color: colour.inkMuted,
  },
  primary: {
    flex: 1,
    minHeight: MINIMUM_TARGET + 6,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colour.accent,
    borderRadius: radius.md,
    ...elevation.resting,
  },
  primaryOff: { backgroundColor: colour.borderStrong },
  primaryText: {
    ...type.heading,
    fontFamily: family.bodySemibold,
    color: colour.onAccent,
  },
});
