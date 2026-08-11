import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import Animated, {
  FadeIn,
  FadeInDown,
  FadeInRight,
  FadeOutLeft,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withSpring,
  withTiming,
} from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Path } from "react-native-svg";

import { Confetti } from "@/components/confetti";
import { GongMascot, type MascotMood } from "@/components/gong-mascot";
import { ListenButton } from "@/components/listen-button";
import { duration } from "@/design/motion";
import { confirm, reject, tick } from "@/design/risk";
import { MINIMUM_TARGET, colour, family, radius, space, type } from "@/design/tokens";
import { finishLine, starsFor, verdictLine } from "@/features/play/encouragement";
import { api } from "@/lib/api/client";
import type { SessionResult } from "@/lib/api/types";
import { useSession } from "@/lib/identity/session";

/**
 * The daily run.
 *
 * One question a page, an answer that reacts the moment it is tapped, and the reason
 * before you move on. Borrowed from the language apps, with three things deliberately
 * left behind:
 *
 * There are no hearts and no lock-out. Getting a question wrong never withholds health
 * information from anybody, which is the whole reason this exists.
 *
 * The streak is counted and celebrated, never used to shame. One missed day a week is
 * forgiven, because people miss days for illness, travel, a dead battery, or the flood we
 * just warned them about.
 *
 * Wrong answers still earn, and still explain. A wrong answer is the best moment somebody
 * will ever have to read why, so that is exactly when the explanation appears.
 */
export default function PlayScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { loading, token, citizen } = useSession();

  useEffect(() => {
    if (!loading && token === null) router.replace("/join");
  }, [loading, token, router]);

  const districtId = citizen?.district_id ?? "";
  const language = citizen?.language ?? "en";

  const [index, setIndex] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [checked, setChecked] = useState(false);
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
    onSuccess: (result) => setOutcome(result),
  });

  const questions = useMemo(() => session.data?.questions ?? [], [session.data]);
  const question = questions[index];
  const total = questions.length;
  const right = checked && picked === question?.correct_option_index;

  const check = () => {
    if (picked === null || question === undefined || checked) return;
    setChecked(true);
    void (picked === question.correct_option_index ? confirm() : reject());
  };

  const advance = () => {
    if (question === undefined || picked === null) return;
    const recorded = [
      ...answers,
      { question_id: question.question_id, selected_option_index: picked },
    ];
    setAnswers(recorded);
    setPicked(null);
    setChecked(false);

    if (index + 1 < total) {
      setIndex(index + 1);
      return;
    }
    submit.mutate(recorded);
  };

  if (outcome !== null) {
    return (
      <Finished
        result={outcome}
        language={language}
        onDone={() => router.replace("/")}
      />
    );
  }

  const mood: MascotMood = !checked ? "waiting" : right ? "right" : "wrong";

  return (
    <View style={[styles.host, { paddingTop: insets.top + space.base }]}>
      <View style={styles.top}>
        <Progress done={checked ? index + 1 : index} total={Math.max(total, 1)} />
        {session.data ? <StreakBadge days={session.data.streak.current_days} /> : null}
      </View>

      <ScrollView
        contentContainerStyle={styles.body}
        keyboardShouldPersistTaps="handled"
      >
        {question === undefined ? (
          <Text style={styles.muted}>
            {session.isError
              ? "Today's questions could not be loaded. They will be here when you are online."
              : "Getting today's questions…"}
          </Text>
        ) : (
          <Animated.View
            key={question.question_id}
            entering={FadeInRight.duration(duration.medium)}
            exiting={FadeOutLeft.duration(duration.short)}
          >
            <View style={styles.askRow}>
              <GongMascot mood={mood} size={56} />
              <View style={styles.askText}>
                <Text style={styles.counter}>
                  Question {index + 1} of {total}
                </Text>
                <Text style={styles.prompt}>{question.prompt}</Text>
              </View>
            </View>

            <View style={styles.listen}>
              <ListenButton
                language={language}
                parts={[{ text: question.prompt, language }]}
              />
            </View>

            <View style={styles.options}>
              {question.options.map((option, optionIndex) => (
                <Option
                  key={option}
                  label={option}
                  chosen={picked === optionIndex}
                  isAnswer={optionIndex === question.correct_option_index}
                  revealed={checked}
                  onPress={() => {
                    if (checked) return;
                    void tick();
                    setPicked(optionIndex);
                  }}
                />
              ))}
            </View>
          </Animated.View>
        )}
      </ScrollView>

      {checked && question !== undefined ? (
        <Animated.View
          entering={FadeInDown.duration(duration.medium)}
          style={[styles.teach, right ? styles.teachRight : styles.teachWrong]}
        >
          <Text
            style={[styles.verdict, right ? styles.verdictRight : styles.verdictWrong]}
          >
            {verdictLine(right, index + question.prompt.length)}
          </Text>
          <Text style={styles.explanation}>{question.explanation}</Text>
        </Animated.View>
      ) : null}

      <View
        style={[styles.footer, { paddingBottom: insets.bottom + space.comfortable }]}
      >
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={
            !checked
              ? "Check this answer"
              : index + 1 < total
                ? "Next question"
                : "Finish the run"
          }
          accessibilityState={{ disabled: picked === null || submit.isPending }}
          disabled={picked === null || submit.isPending}
          onPress={checked ? advance : check}
          style={[
            styles.primary,
            picked === null && styles.primaryOff,
            checked && (right ? styles.primaryRight : styles.primaryWrong),
          ]}
        >
          <Text style={styles.primaryText}>
            {submit.isPending
              ? "Counting up…"
              : !checked
                ? "Check"
                : index + 1 < total
                  ? "Continue"
                  : "Finish"}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

/** One answer. The whole row is the target, and it shows its state after the check. */
function Option({
  label,
  chosen,
  isAnswer,
  revealed,
  onPress,
}: {
  label: string;
  chosen: boolean;
  isAnswer: boolean;
  revealed: boolean;
  onPress: () => void;
}) {
  const reduceMotion = useReducedMotion();
  const press = useSharedValue(0);

  const style = useAnimatedStyle(() => ({
    transform: [{ scale: reduceMotion ? 1 : 1 - press.value * 0.025 }],
  }));

  const showRight = revealed && isAnswer;
  const showWrong = revealed && chosen && !isAnswer;

  return (
    <Animated.View style={style}>
      <Pressable
        accessibilityRole="radio"
        accessibilityState={{ selected: chosen, disabled: revealed }}
        accessibilityLabel={
          showRight
            ? `${label}. Correct answer`
            : showWrong
              ? `${label}. Not correct`
              : label
        }
        onPressIn={() => {
          press.value = reduceMotion
            ? withTiming(1, { duration: 60 })
            : withSpring(1, { damping: 18, stiffness: 420 });
        }}
        onPressOut={() => {
          press.value = withSpring(0, { damping: 18, stiffness: 420 });
        }}
        onPress={onPress}
        style={[
          styles.option,
          chosen && !revealed && styles.optionChosen,
          showRight && styles.optionRight,
          showWrong && styles.optionWrong,
        ]}
      >
        <Text
          style={[
            styles.optionText,
            chosen && !revealed && styles.optionTextChosen,
            showRight && styles.optionTextRight,
            showWrong && styles.optionTextWrong,
          ]}
        >
          {label}
        </Text>
        {showRight ? <Tick /> : null}
      </Pressable>
    </Animated.View>
  );
}

function Progress({ done, total }: { done: number; total: number }) {
  const share = Math.min(done / total, 1);
  const width = useSharedValue(0);

  useEffect(() => {
    width.value = withSpring(share, { damping: 18, stiffness: 140 });
  }, [share, width]);

  const style = useAnimatedStyle(() => ({ width: `${width.value * 100}%` }));

  return (
    <View
      style={styles.track}
      accessibilityRole="progressbar"
      accessibilityLabel={`${done} of ${total} answered`}
    >
      <Animated.View style={[styles.fill, style]} />
    </View>
  );
}

function StreakBadge({ days }: { days: number }) {
  if (days <= 0) return null;
  return (
    <View style={styles.streak} accessibilityLabel={`${days} day streak`}>
      <Flame />
      <Text style={styles.streakText}>{days}</Text>
    </View>
  );
}

/** The end of the run: stars, points counting up, and every explanation kept. */
function Finished({
  result,
  language,
  onDone,
}: {
  result: SessionResult;
  language: string;
  onDone: () => void;
}) {
  const insets = useSafeAreaInsets();
  const stars = starsFor(result.correct_count, result.total);

  useEffect(() => {
    void confirm();
  }, []);

  return (
    <View style={styles.host}>
      <Confetti running={result.correct_count > 0} />
      <ScrollView
        contentContainerStyle={[
          styles.body,
          { paddingTop: insets.top + space.roomy, paddingBottom: space.section },
        ]}
      >
        <Animated.View
          entering={FadeIn.duration(duration.medium)}
          style={styles.finishTop}
        >
          <GongMascot mood="celebrating" size={84} />
          <Stars filled={stars} />
          <Text style={styles.score}>
            {result.correct_count} of {result.total}
          </Text>
          <Text style={styles.finishLine}>
            {finishLine(result.correct_count, result.total, result.total_points)}
          </Text>
        </Animated.View>

        <View style={styles.awards}>
          <CountUp value={result.points_awarded} label="XP earned" prefix="+" />
          <CountUp value={result.total_points} label="XP in total" />
          <CountUp
            value={result.streak.current_days}
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
              {answer.correct ? "Correct" : "Worth remembering"}
            </Text>
            <Text style={styles.reviewText}>{answer.explanation}</Text>
          </View>
        ))}

        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Back to today"
          onPress={onDone}
          style={[styles.primary, styles.finishButton]}
        >
          <Text style={styles.primaryText}>Back to today</Text>
        </Pressable>
      </ScrollView>
    </View>
  );
}

/** Numbers that climb, because a total that simply appears is not felt. */
function CountUp({
  value,
  label,
  prefix = "",
}: {
  value: number;
  label: string;
  prefix?: string;
}) {
  const reduceMotion = useReducedMotion();
  const [shown, setShown] = useState(reduceMotion ? value : 0);

  useEffect(() => {
    if (reduceMotion || value <= 0) {
      setShown(value);
      return;
    }
    const steps = Math.min(value, 24);
    const stepSize = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += 1;
      setShown(current >= steps ? value : Math.round(stepSize * current));
      if (current >= steps) clearInterval(timer);
    }, 34);
    return () => clearInterval(timer);
  }, [value, reduceMotion]);

  return (
    <View style={styles.award}>
      <Text style={styles.awardValue}>
        {prefix}
        {shown}
      </Text>
      <Text style={styles.awardLabel}>{label}</Text>
    </View>
  );
}

function Stars({ filled }: { filled: number }) {
  return (
    <View style={styles.stars} accessibilityLabel={`${filled} out of 5 stars`}>
      {Array.from({ length: 5 }, (_, index) => (
        <Animated.View
          key={index}
          entering={FadeInDown.delay(120 + index * 90).duration(duration.medium)}
        >
          <Star filled={index < filled} />
        </Animated.View>
      ))}
    </View>
  );
}

function Star({ filled }: { filled: boolean }) {
  return (
    <Svg width={30} height={30} viewBox="0 0 24 24">
      <Path
        d="m12 2.6 2.9 5.9 6.5.9-4.7 4.6 1.1 6.5-5.8-3-5.8 3 1.1-6.5L2.6 9.4l6.5-.9z"
        fill={filled ? colour.ochre : "transparent"}
        stroke={filled ? colour.ochre : colour.border}
        strokeWidth={1.6}
        strokeLinejoin="round"
      />
    </Svg>
  );
}

function Tick() {
  return (
    <Svg width={20} height={20} viewBox="0 0 24 24" fill="none">
      <Path
        d="m5 13 4 4L19 7"
        stroke={colour.riskLow}
        strokeWidth={2.8}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

function Flame() {
  return (
    <Svg width={16} height={16} viewBox="0 0 24 24">
      <Path
        d="M12 2c1.5 3.5-1 5 .5 7.5C14 12 16 10 16 10s2 2.2 2 5a6 6 0 1 1-12 0c0-3.6 2.8-5.5 3.5-7.5C10.2 5.4 10 3.4 12 2Z"
        fill={colour.riskModerate}
      />
    </Svg>
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
    height: 12,
    borderRadius: radius.pill,
    backgroundColor: colour.border,
    overflow: "hidden",
  },
  fill: { height: "100%", backgroundColor: colour.accent, borderRadius: radius.pill },
  streak: { flexDirection: "row", alignItems: "center", gap: 3 },
  streakText: {
    ...type.body,
    fontFamily: family.bodySemibold,
    color: colour.riskModerate,
  },
  body: { paddingHorizontal: space.comfortable, paddingBottom: space.roomy },
  askRow: { flexDirection: "row", alignItems: "flex-start", gap: space.base },
  askText: { flex: 1 },
  counter: {
    ...type.overline,
    fontFamily: family.bodyMedium,
    color: colour.inkFaint,
  },
  prompt: {
    ...type.title,
    fontFamily: family.display,
    color: colour.ink,
    marginTop: space.tight,
  },
  listen: { marginTop: space.base },
  options: { marginTop: space.roomy, gap: space.snug },
  option: {
    minHeight: MINIMUM_TARGET + 16,
    flexDirection: "row",
    alignItems: "center",
    gap: space.base,
    backgroundColor: colour.surface,
    borderWidth: 2,
    borderColor: colour.border,
    borderRadius: radius.lg,
    paddingHorizontal: space.comfortable,
    paddingVertical: space.base,
  },
  optionChosen: { borderColor: colour.accent, backgroundColor: colour.accentSubtle },
  optionRight: { borderColor: colour.riskLow, backgroundColor: colour.riskLowSurface },
  optionWrong: {
    borderColor: colour.riskHigh,
    backgroundColor: colour.riskHighSurface,
  },
  optionText: {
    ...type.body,
    fontFamily: family.bodyMedium,
    color: colour.ink,
    flex: 1,
  },
  optionTextChosen: { color: colour.accentPressed },
  optionTextRight: { color: colour.ink },
  optionTextWrong: { color: colour.ink },
  muted: {
    ...type.body,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: space.section,
  },
  teach: {
    marginHorizontal: space.comfortable,
    borderRadius: radius.lg,
    borderLeftWidth: 4,
    paddingHorizontal: space.comfortable,
    paddingVertical: space.base,
  },
  teachRight: {
    backgroundColor: colour.riskLowSurface,
    borderLeftColor: colour.riskLow,
  },
  teachWrong: {
    backgroundColor: colour.riskModerateSurface,
    borderLeftColor: colour.riskModerate,
  },
  verdict: { ...type.heading, fontFamily: family.bodySemibold },
  verdictRight: { color: colour.riskLow },
  verdictWrong: { color: colour.riskModerate },
  explanation: {
    ...type.small,
    fontFamily: family.body,
    color: colour.ink,
    marginTop: space.tight,
  },
  footer: {
    paddingHorizontal: space.comfortable,
    paddingTop: space.base,
  },
  primary: {
    minHeight: MINIMUM_TARGET + 12,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colour.accent,
    borderRadius: radius.lg,
  },
  primaryOff: { backgroundColor: colour.borderStrong },
  primaryRight: { backgroundColor: colour.riskLow },
  primaryWrong: { backgroundColor: colour.riskModerate },
  primaryText: {
    ...type.heading,
    fontFamily: family.bodySemibold,
    color: colour.onAccent,
  },
  finishTop: { alignItems: "center" },
  stars: { flexDirection: "row", gap: space.tight, marginTop: space.base },
  score: {
    ...type.verdict,
    fontFamily: family.display,
    color: colour.accent,
    marginTop: space.base,
  },
  finishLine: {
    ...type.body,
    fontFamily: family.body,
    color: colour.inkMuted,
    textAlign: "center",
    marginTop: space.tight,
  },
  awards: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: space.base,
    marginTop: space.generous,
  },
  award: { flexShrink: 1 },
  awardValue: { ...type.display, fontFamily: family.display, color: colour.ink },
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
  finishButton: { marginTop: space.section },
});
