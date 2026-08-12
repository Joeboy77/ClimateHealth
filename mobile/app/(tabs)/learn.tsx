import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import Animated, { FadeIn } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { duration } from "@/design/motion";
import { confirm, reject, tick } from "@/design/risk";
import { MINIMUM_TARGET, colour, family, radius, space, type } from "@/design/tokens";
import { ListenButton } from "@/components/listen-button";
import { api } from "@/lib/api/client";
import type { GuardianTier } from "@/lib/api/types";
import { useSession } from "@/lib/identity/session";

/**
 * Learn.
 *
 * Two things, in the order that matters: the lesson today's weather asked for, then the
 * question that checks it landed. The lesson is written for the reader's age band, so a
 * nine-year-old and a grandmother in the same district read different words about the
 * same standing water.
 *
 * Deliberately quiet: one fade as content arrives, and nothing that moves while somebody
 * is reading.
 */
export default function LearnScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { loading, token, citizen } = useSession();

  useEffect(() => {
    if (!loading && token === null) router.replace("/join");
  }, [loading, token, router]);

  const districtId = citizen?.district_id ?? "";

  const lesson = useQuery({
    queryKey: ["lesson", districtId],
    queryFn: () => api.lessonToday(token ?? "", districtId),
    enabled: token !== null && districtId !== "",
  });

  const quiz = useQuery({
    queryKey: ["quiz", districtId],
    queryFn: () => api.dailyQuiz(token ?? "", districtId),
    enabled: token !== null && districtId !== "",
  });

  return (
    <ScrollView
      style={styles.host}
      contentContainerStyle={[
        styles.content,
        { paddingTop: insets.top + space.roomy, paddingBottom: space.section },
      ]}
    >
      {lesson.data ? (
        <Animated.View entering={FadeIn.duration(duration.medium)}>
          <Text style={styles.eyebrow}>
            Today in {lesson.data.district_name} · {lesson.data.tier_name}
          </Text>
          <Text style={styles.title}>{lesson.data.lesson.title}</Text>
          <Text style={[styles.body, elderly(lesson.data.tier) && styles.bodyLarge]}>
            {lesson.data.lesson.body}
          </Text>

          <View style={styles.action}>
            <Text style={styles.actionLabel}>DO THIS</Text>
            <Text style={styles.actionText}>{lesson.data.lesson.action}</Text>
          </View>

          <View style={styles.listen}>
            <ListenButton
              language={citizen?.language ?? "en"}
              prominent={elderly(lesson.data.tier)}
              parts={[
                { text: lesson.data.lesson.title, language: citizen?.language ?? "en" },
                { text: lesson.data.lesson.body, language: citizen?.language ?? "en" },
                {
                  text: lesson.data.lesson.action,
                  language: citizen?.language ?? "en",
                },
              ]}
            />
          </View>

          <Text style={styles.meta}>
            {lesson.data.lesson.read_seconds} seconds to read · chosen because the
            engine raised {lesson.data.triggered_by.replace(/_/g, " ")} here
          </Text>
        </Animated.View>
      ) : lesson.isError ? (
        <Text style={styles.body}>
          Today&rsquo;s lesson could not be loaded. It will be here when you are back
          online.
        </Text>
      ) : (
        <Text style={styles.body}>Loading today&rsquo;s lesson…</Text>
      )}

      {quiz.data && citizen ? (
        <Quiz
          token={token ?? ""}
          userId={citizen.user_id}
          questionId={quiz.data.question_id}
          prompt={quiz.data.prompt}
          options={quiz.data.options}
        />
      ) : null}
    </ScrollView>
  );
}

/** Voice-First readers get larger body text by default, per proposal section 11.4. */
function elderly(tier: GuardianTier): boolean {
  return tier === "voice_first";
}

function Quiz({
  token,
  userId,
  questionId,
  prompt,
  options,
}: {
  token: string;
  userId: string;
  questionId: string;
  prompt: string;
  options: readonly string[];
}) {
  const [chosen, setChosen] = useState<number | null>(null);

  const answer = useMutation({
    mutationFn: (index: number) => api.answerQuiz(token, userId, questionId, index),
    onSuccess: async (result) => {
      if (result.correct) await confirm();
      else await reject();
    },
  });

  return (
    <View style={styles.quiz}>
      <Text style={styles.quizLabel}>ONE QUESTION</Text>
      <Text style={styles.quizPrompt}>{prompt}</Text>

      {options.map((option, index) => {
        const picked = chosen === index;
        const settled = answer.data !== undefined;
        const isAnswer = settled && answer.data.correct_option_index === index;
        const wrongPick = settled && picked && !answer.data.correct;

        return (
          <Pressable
            key={option}
            accessibilityRole="radio"
            accessibilityState={{ selected: picked, disabled: settled }}
            accessibilityLabel={option}
            disabled={settled || answer.isPending}
            onPress={() => {
              void tick();
              setChosen(index);
              answer.mutate(index);
            }}
            style={[
              styles.option,
              picked && !settled && styles.optionPicked,
              isAnswer && styles.optionRight,
              wrongPick && styles.optionWrong,
            ]}
          >
            <Text style={styles.optionText}>{option}</Text>
            {isAnswer ? <Text style={styles.optionMark}>Correct</Text> : null}
          </Pressable>
        );
      })}

      {answer.data ? (
        <Animated.View entering={FadeIn.duration(duration.medium)}>
          <Text style={styles.explanation}>{answer.data.explanation}</Text>
          <Text style={styles.points}>
            {answer.data.points_awarded > 0
              ? `+${answer.data.points_awarded} points · ${answer.data.total_points} in total`
              : `Already answered today · ${answer.data.total_points} points in total`}
          </Text>
        </Animated.View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  host: { flex: 1, backgroundColor: colour.canvas },
  content: { paddingHorizontal: space.comfortable },
  eyebrow: {
    ...type.overline,
    fontFamily: family.bodyMedium,
    color: colour.inkFaint,
    textTransform: "uppercase",
  },
  title: {
    ...type.display,
    fontFamily: family.display,
    color: colour.ink,
    marginTop: space.snug,
  },
  body: {
    ...type.body,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: space.base,
  },
  bodyLarge: { fontSize: 19, lineHeight: 30 },
  listen: { marginTop: space.roomy },
  action: {
    marginTop: space.roomy,
    borderLeftWidth: 3,
    borderLeftColor: colour.accent,
    backgroundColor: colour.surface,
    borderTopRightRadius: radius.md,
    borderBottomRightRadius: radius.md,
    paddingHorizontal: space.comfortable,
    paddingVertical: space.base,
  },
  actionLabel: {
    ...type.overline,
    fontFamily: family.bodyMedium,
    color: colour.inkFaint,
  },
  actionText: {
    ...type.heading,
    fontFamily: family.bodyMedium,
    color: colour.ink,
    marginTop: space.tight,
  },
  meta: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.inkFaint,
    marginTop: space.base,
  },
  quiz: {
    marginTop: space.section,
    borderTopWidth: 1,
    borderTopColor: colour.border,
    paddingTop: space.roomy,
  },
  quizLabel: {
    ...type.overline,
    fontFamily: family.bodyMedium,
    color: colour.inkFaint,
  },
  quizPrompt: {
    ...type.title,
    fontFamily: family.bodySemibold,
    color: colour.ink,
    marginTop: space.snug,
    marginBottom: space.base,
  },
  option: {
    minHeight: MINIMUM_TARGET + 6,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: space.base,
    backgroundColor: colour.surface,
    borderWidth: 1.5,
    borderColor: colour.border,
    borderRadius: radius.md,
    paddingHorizontal: space.comfortable,
    paddingVertical: space.base,
    marginBottom: space.snug,
  },
  optionPicked: { borderColor: colour.accent },
  optionRight: { borderColor: colour.riskLow, backgroundColor: colour.riskLowSurface },
  optionWrong: {
    borderColor: colour.riskSevere,
    backgroundColor: colour.riskSevereSurface,
  },
  optionText: { ...type.body, fontFamily: family.body, color: colour.ink, flex: 1 },
  optionMark: {
    ...type.caption,
    fontFamily: family.bodySemibold,
    color: colour.riskLow,
  },
  explanation: {
    ...type.body,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: space.base,
  },
  points: {
    ...type.small,
    fontFamily: family.bodyMedium,
    color: colour.accentPressed,
    marginTop: space.snug,
  },
});
