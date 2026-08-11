import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import Animated, {
  FadeIn,
  FadeInDown,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withSpring,
  withTiming,
} from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { ListenButton } from "@/components/listen-button";
import { duration } from "@/design/motion";
import { confirm, reject, tick } from "@/design/risk";
import { MINIMUM_TARGET, colour, family, radius, space, type } from "@/design/tokens";
import { api } from "@/lib/api/client";
import type { SessionResult } from "@/lib/api/types";
import { useSession } from "@/lib/identity/session";

/**
 * The daily run.
 *
 * One question at a time, a big target for every answer, and the verdict the moment you
 * choose. Borrowed from the language apps, with three things deliberately left behind:
 *
 * There are no hearts and no lock-out. Getting a question wrong never withholds health
 * information from anybody, which is the whole reason this application exists.
 *
 * The streak is counted and celebrated, never used to shame. One missed day a week is
 * forgiven, because people miss days for illness, travel, a dead battery, or the flood we
 * just warned them about.
 *
 * The run is sized by age band, so a nine-year-old gets five questions and an elder
 * reading with the audio on gets two.
 */
export default function PlayScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { loading, token, citizen } = useSession();

  useEffect(() => {
    if (!loading && token === null) router.replace("/join");
  }, [loading, token, router]);

  const districtId = citizen?.district_id ?? "";
  const [index, setIndex] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [answers, setAnswers] = useState<
    { question_id: string; selected_option_index: number }[]
  >([]);
  const [outcome, setOutcome] = useState<SessionResult | null>(null);

  const session = useQuery({
    queryKey: ["play-session", districtId],
    queryFn: () => api.quizSession(token ?? "", districtId),
    enabled: token !== null && districtId !== "",
  });

  const submit = useMutation({
    mutationFn: (finished: { question_id: string; selected_option_index: number }[]) =>
      api.submitSession(token ?? "", citizen?.user_id ?? "", finished),
    onSuccess: async (result) => {
      await confirm();
      setOutcome(result);
    },
  });

  const questions = useMemo(() => session.data?.questions ?? [], [session.data]);
  const question = questions[index];
  const total = questions.length;

  const choose = (option: number) => {
    if (picked !== null || question === undefined) return;
    void tick();
    setPicked(option);
  };

  const next = () => {
    if (picked === null || question === undefined) return;
    const recorded = [
      ...answers,
      { question_id: question.question_id, selected_option_index: picked },
    ];
    setAnswers(recorded);
    setPicked(null);

    if (index + 1 < total) {
      setIndex(index + 1);
      return;
    }
    submit.mutate(recorded);
  };

  if (outcome !== null && session.data) {
    return (
      <Finished
        result={outcome}
        onDone={() => router.replace("/")}
        language={citizen?.language ?? "en"}
      />
    );
  }

  return (
    <View style={[styles.host, { paddingTop: insets.top + space.base }]}>
      <View style={styles.top}>
        <Progress done={index} total={Math.max(total, 1)} />
        {session.data ? <Streak days={session.data.streak.current_days} /> : null}
      </View>

      <ScrollView contentContainerStyle={styles.body}>
        {question === undefined ? (
          <Text style={styles.muted}>
            {session.isError
              ? "Today's questions could not be loaded. Try again when you are online."
              : "Getting today's questions…"}
          </Text>
        ) : (
          <Animated.View
            key={question.question_id}
            entering={FadeIn.duration(duration.short)}
          >
            <Text style={styles.counter}>
              Question {index + 1} of {total}
            </Text>
            <Text style={styles.prompt}>{question.prompt}</Text>

            <View style={styles.listen}>
              <ListenButton
                language={citizen?.language ?? "en"}
                parts={[{ text: question.prompt, language: citizen?.language ?? "en" }]}
              />
            </View>

            <View style={styles.options}>
              {question.options.map((option, optionIndex) => (
                <Option
                  key={option}
                  label={option}
                  chosen={picked === optionIndex}
                  locked={picked !== null}
                  onPress={() => choose(optionIndex)}
                />
              ))}
            </View>
          </Animated.View>
        )}
      </ScrollView>

      <View
        style={[styles.footer, { paddingBottom: insets.bottom + space.comfortable }]}
      >
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={index + 1 < total ? "Next question" : "Finish"}
          accessibilityState={{ disabled: picked === null || submit.isPending }}
          disabled={picked === null || submit.isPending}
          onPress={next}
          style={[styles.primary, picked === null && styles.primaryOff]}
        >
          <Text style={styles.primaryText}>
            {submit.isPending ? "Checking…" : index + 1 < total ? "Check" : "Finish"}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

/** One answer. Large, and the whole row is the target. */
function Option({
  label,
  chosen,
  locked,
  onPress,
}: {
  label: string;
  chosen: boolean;
  locked: boolean;
  onPress: () => void;
}) {
  const reduceMotion = useReducedMotion();
  const press = useSharedValue(0);

  const style = useAnimatedStyle(() => ({
    transform: [{ scale: reduceMotion ? 1 : 1 - press.value * 0.02 }],
  }));

  return (
    <Animated.View style={style}>
      <Pressable
        accessibilityRole="radio"
        accessibilityState={{ selected: chosen, disabled: locked && !chosen }}
        accessibilityLabel={label}
        onPressIn={() => {
          press.value = reduceMotion
            ? withTiming(1, { duration: 60 })
            : withSpring(1, { damping: 18, stiffness: 400 });
        }}
        onPressOut={() => {
          press.value = withSpring(0, { damping: 18, stiffness: 400 });
        }}
        onPress={onPress}
        style={[styles.option, chosen && styles.optionChosen]}
      >
        <Text style={[styles.optionText, chosen && styles.optionTextChosen]}>
          {label}
        </Text>
      </Pressable>
    </Animated.View>
  );
}

function Progress({ done, total }: { done: number; total: number }) {
  const share = Math.min(done / total, 1);
  return (
    <View
      style={styles.track}
      accessibilityRole="progressbar"
      accessibilityLabel={`Question ${done + 1} of ${total}`}
    >
      <View style={[styles.fill, { width: `${share * 100}%` }]} />
    </View>
  );
}

function Streak({ days }: { days: number }) {
  if (days <= 0) return null;
  return (
    <Text style={styles.streak} accessibilityLabel={`${days} day streak`}>
      {days} day{days === 1 ? "" : "s"} running
    </Text>
  );
}

/**
 * The end of the run. Every explanation is shown whether the answer was right or wrong,
 * because the explanation is the point and a wrong answer is the best moment to read it.
 */
function Finished({
  result,
  onDone,
  language,
}: {
  result: SessionResult;
  onDone: () => void;
  language: string;
}) {
  const insets = useSafeAreaInsets();

  useEffect(() => {
    if (!result.perfect) void reject();
  }, [result.perfect]);

  return (
    <ScrollView
      style={styles.host}
      contentContainerStyle={[
        styles.body,
        { paddingTop: insets.top + space.section, paddingBottom: space.section },
      ]}
    >
      <Animated.View entering={FadeInDown.duration(duration.medium)}>
        <Text style={styles.score}>
          {result.correct_count} of {result.total}
        </Text>
        <Text style={styles.scoreLabel}>
          {result.perfect ? "Every one right" : "Every answer still earns something"}
        </Text>

        <View style={styles.awards}>
          <Award value={`+${result.points_awarded}`} label="points earned" />
          <Award value={String(result.total_points)} label="points in total" />
          <Award
            value={String(result.streak.current_days)}
            label={result.streak.current_days === 1 ? "day running" : "days running"}
          />
        </View>

        <View style={styles.listen}>
          <ListenButton
            language={language as "en"}
            parts={result.answers.map((answer) => ({
              text: answer.explanation,
              language: language as "en",
            }))}
          />
        </View>

        {result.answers.map((answer) => (
          <View
            key={answer.question_id}
            style={[
              styles.review,
              answer.correct ? styles.reviewRight : styles.reviewWrong,
            ]}
          >
            <Text style={styles.reviewVerdict}>
              {answer.correct ? "Correct" : "Not quite"}
            </Text>
            <Text style={styles.reviewText}>{answer.explanation}</Text>
          </View>
        ))}
      </Animated.View>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Back to today"
        onPress={onDone}
        style={[styles.primary, styles.finishButton]}
      >
        <Text style={styles.primaryText}>Back to today</Text>
      </Pressable>
    </ScrollView>
  );
}

function Award({ value, label }: { value: string; label: string }) {
  return (
    <View style={styles.award}>
      <Text style={styles.awardValue}>{value}</Text>
      <Text style={styles.awardLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  host: { flex: 1, backgroundColor: colour.canvas },
  top: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.base,
    paddingHorizontal: space.comfortable,
    paddingBottom: space.base,
  },
  track: {
    flex: 1,
    height: 10,
    borderRadius: radius.pill,
    backgroundColor: colour.border,
    overflow: "hidden",
  },
  fill: { height: "100%", backgroundColor: colour.accent, borderRadius: radius.pill },
  streak: {
    ...type.small,
    fontFamily: family.bodySemibold,
    color: colour.riskModerate,
  },
  body: { paddingHorizontal: space.comfortable, paddingBottom: space.roomy },
  counter: {
    ...type.overline,
    fontFamily: family.bodyMedium,
    color: colour.inkFaint,
    marginTop: space.base,
  },
  prompt: {
    ...type.display,
    fontFamily: family.display,
    color: colour.ink,
    marginTop: space.snug,
  },
  listen: { marginTop: space.base },
  options: { marginTop: space.roomy, gap: space.snug },
  option: {
    minHeight: MINIMUM_TARGET + 14,
    justifyContent: "center",
    backgroundColor: colour.surface,
    borderWidth: 2,
    borderColor: colour.border,
    borderRadius: radius.lg,
    paddingHorizontal: space.comfortable,
    paddingVertical: space.base,
  },
  optionChosen: { borderColor: colour.accent, backgroundColor: colour.accentSubtle },
  optionText: { ...type.body, fontFamily: family.bodyMedium, color: colour.ink },
  optionTextChosen: { color: colour.accentPressed },
  muted: {
    ...type.body,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: space.section,
  },
  footer: {
    paddingHorizontal: space.comfortable,
    paddingTop: space.base,
    borderTopWidth: 1,
    borderTopColor: colour.border,
  },
  primary: {
    minHeight: MINIMUM_TARGET + 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colour.accent,
    borderRadius: radius.lg,
  },
  primaryOff: { backgroundColor: colour.borderStrong },
  primaryText: {
    ...type.heading,
    fontFamily: family.bodySemibold,
    color: colour.onAccent,
  },
  finishButton: { marginTop: space.roomy },
  score: { ...type.verdict, fontFamily: family.display, color: colour.accent },
  scoreLabel: {
    ...type.body,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: space.tight,
  },
  awards: { flexDirection: "row", gap: space.roomy, marginTop: space.roomy },
  award: { flexShrink: 1 },
  awardValue: { ...type.title, fontFamily: family.bodySemibold, color: colour.ink },
  awardLabel: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: 2,
  },
  review: {
    marginTop: space.base,
    borderRadius: radius.md,
    borderLeftWidth: 4,
    paddingHorizontal: space.comfortable,
    paddingVertical: space.base,
    backgroundColor: colour.surface,
  },
  reviewRight: { borderLeftColor: colour.riskLow },
  reviewWrong: { borderLeftColor: colour.riskModerate },
  reviewVerdict: {
    ...type.overline,
    fontFamily: family.bodySemibold,
    color: colour.inkFaint,
  },
  reviewText: {
    ...type.small,
    fontFamily: family.body,
    color: colour.ink,
    marginTop: space.tight,
  },
});
