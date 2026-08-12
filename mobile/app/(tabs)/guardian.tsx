import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import Animated, { FadeIn } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { duration } from "@/design/motion";
import { MINIMUM_TARGET, colour, family, radius, space, type } from "@/design/tokens";
import { api } from "@/lib/api/client";
import type { GuardianLevel } from "@/lib/api/types";
import { useSession } from "@/lib/identity/session";
import {
  disableReminder,
  enableReminder,
  reminderEnabled,
} from "@/lib/reminders/daily";
import { setSoundMuted, soundMuted } from "@/lib/sound/quiz-sounds";
import { optionsReadAloud, setOptionsReadAloud } from "@/lib/speech/speak";
import { SettingSwitch } from "@/components/setting-switch";

/**
 * The Guardian card.
 *
 * Points are shown next to what they unlock, never on their own. Proposal section 12: the
 * reward is health insurance registration, because recognition alone does not pay for a
 * clinic visit. Under-18s are exempt from premiums already, so their card says what they
 * actually earn instead of dangling something meaningless.
 */
export default function GuardianScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { loading, token, citizen } = useSession();

  useEffect(() => {
    if (!loading && token === null) router.replace("/join");
  }, [loading, token, router]);

  const userId = citizen?.user_id ?? "";

  const profile = useQuery({
    queryKey: ["guardian", userId],
    queryFn: () => api.guardian(token ?? "", userId),
    enabled: token !== null && userId !== "",
  });

  const rewards = useQuery({
    queryKey: ["rewards", userId],
    queryFn: () => api.rewards(token ?? "", userId),
    enabled: token !== null && userId !== "",
  });

  const shield = useQuery({
    queryKey: ["shield", citizen?.district_id],
    queryFn: () => api.shield(token ?? "", citizen?.district_id ?? ""),
    enabled: token !== null && (citizen?.district_id ?? "") !== "",
  });

  const toNext = rewards.data?.points_to_next_level ?? 0;
  const current = rewards.data?.current_level;
  const next = rewards.data?.next_level;

  const progress =
    current && next
      ? Math.min(
          Math.max(
            ((rewards.data?.points ?? 0) - current.minimum_points) /
              Math.max(next.minimum_points - current.minimum_points, 1),
            0,
          ),
          1,
        )
      : 1;

  return (
    <ScrollView
      style={styles.host}
      contentContainerStyle={[
        styles.content,
        { paddingTop: insets.top + space.roomy, paddingBottom: space.section },
      ]}
    >
      {profile.data && citizen ? (
        <Animated.View entering={FadeIn.duration(duration.medium)}>
          <Text style={styles.eyebrow}>CLIMATE GUARDIAN · {citizen.tier_name}</Text>
          <Text style={styles.name}>{profile.data.display_name}</Text>

          <View style={styles.figures}>
            <Figure value={String(profile.data.points)} label="points" />
            <Figure value={profile.data.level.name} label="level" small />
            <Figure
              value={String(profile.data.missions_completed)}
              label="missions done"
            />
          </View>

          {next ? (
            <View style={styles.progressBlock}>
              <View style={styles.track}>
                <View style={[styles.fill, { width: `${progress * 100}%` }]} />
              </View>
              <Text style={styles.progressText}>
                {toNext} more {toNext === 1 ? "point" : "points"} to {next.name}
              </Text>
            </View>
          ) : (
            <Text style={styles.progressText}>
              You have reached the top level in your district.
            </Text>
          )}
        </Animated.View>
      ) : (
        <Text style={styles.muted}>Loading your card…</Text>
      )}

      {rewards.data ? (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>WHAT POINTS UNLOCK</Text>
          {citizen?.health_rewards_available === false ? (
            <Text style={styles.muted}>
              Under-18s are already exempt from health insurance premiums, so your
              points earn recognition and class rewards rather than cover you do not
              need.
            </Text>
          ) : null}
          {rewards.data.ladder.map((level: GuardianLevel) => (
            <Level
              key={level.name}
              level={level}
              reached={(rewards.data?.points ?? 0) >= level.minimum_points}
            />
          ))}
        </View>
      ) : null}

      <Settings />

      <SignOut />

      {shield.data ? (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>YOUR DISTRICT&rsquo;S SHIELD</Text>
          <Text style={styles.shield}>
            {shield.data.district_name} is {shield.data.status.replace(/_/g, " ")}
          </Text>
          <Text style={styles.muted}>
            {shield.data.active_guardians} Guardians · {shield.data.community_reports}{" "}
            reports · {shield.data.missions_completed} missions
          </Text>
        </View>
      ) : null}
    </ScrollView>
  );
}

/**
 * Signing out.
 *
 * Confirmed first, because a Guardian card holds a streak somebody has kept for weeks
 * and a mis-tap that appears to throw it away is alarming even though the points are
 * safe on the server. The wording says so plainly.
 */
function SignOut() {
  const router = useRouter();
  const { leave, citizen } = useSession();

  const confirmAndLeave = () => {
    Alert.alert(
      "Sign out of Dawuro?",
      "Your points and streak stay on your account. Sign back in with your phone number and password to pick them up.",
      [
        { text: "Stay signed in", style: "cancel" },
        {
          text: "Sign out",
          style: "destructive",
          onPress: () => {
            void leave().then(() => router.replace("/login"));
          },
        },
      ],
    );
  };

  return (
    <View style={styles.section}>
      <Text style={styles.sectionLabel}>ACCOUNT</Text>
      {citizen ? (
        <Text style={styles.muted}>Signed in as {citizen.display_name}.</Text>
      ) : null}
      <Pressable
        onPress={confirmAndLeave}
        accessibilityRole="button"
        accessibilityLabel="Sign out of Dawuro"
        style={styles.signOut}
      >
        <Text style={styles.signOutText}>Sign out</Text>
      </Pressable>
    </View>
  );
}

/** Both toggles are off-by-default and opt-in. Nothing here nags anybody. */
function Settings() {
  const [reminder, setReminder] = useState(false);
  const [sound, setSound] = useState(true);
  const [spoken, setSpoken] = useState(true);

  useEffect(() => {
    setReminder(reminderEnabled());
    setSound(!soundMuted());
    setSpoken(optionsReadAloud());
  }, []);

  return (
    <View style={styles.section}>
      <Text style={styles.sectionLabel}>SETTINGS</Text>
      <SettingSwitch
        label="Quiz sounds"
        description="A chime for a right answer, a softer note for a wrong one."
        value={sound}
        onChange={(next) => {
          setSound(next);
          setSoundMuted(!next);
        }}
      />
      <SettingSwitch
        label="Read answers aloud"
        description="Hear the answer you tapped before you commit to it."
        value={spoken}
        onChange={(next) => {
          setSpoken(next);
          setOptionsReadAloud(next);
        }}
      />
      <SettingSwitch
        label="Morning reminder"
        description="One notification at 7am, never more. Turn it off any time."
        value={reminder}
        onChange={(next) => {
          if (!next) {
            setReminder(false);
            void disableReminder();
            return;
          }
          void enableReminder().then(setReminder);
        }}
      />
    </View>
  );
}

function Figure({
  value,
  label,
  small = false,
}: {
  value: string;
  label: string;
  small?: boolean;
}) {
  return (
    <View style={styles.figure}>
      <Text style={[styles.figureValue, small && styles.figureValueSmall]}>
        {value}
      </Text>
      <Text style={styles.figureLabel}>{label}</Text>
    </View>
  );
}

function Level({ level, reached }: { level: GuardianLevel; reached: boolean }) {
  return (
    <View style={[styles.level, reached && styles.levelReached]}>
      <View style={styles.levelText}>
        <Text style={[styles.levelName, reached && styles.levelNameReached]}>
          {level.name}
        </Text>
        <Text style={styles.muted}>{level.unlocks}</Text>
      </View>
      <Text style={styles.levelPoints}>{level.minimum_points}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  signOut: {
    minHeight: MINIMUM_TARGET,
    marginTop: space.base,
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: colour.riskSevere,
    alignItems: "center",
    justifyContent: "center",
  },
  signOutText: {
    ...type.body,
    fontFamily: family.bodySemibold,
    color: colour.riskSevere,
  },
  host: { flex: 1, backgroundColor: colour.canvas },
  content: { paddingHorizontal: space.comfortable },
  eyebrow: {
    ...type.overline,
    fontFamily: family.bodyMedium,
    color: colour.inkFaint,
  },
  name: {
    ...type.display,
    fontFamily: family.display,
    color: colour.ink,
    marginTop: space.snug,
  },
  figures: { flexDirection: "row", gap: space.roomy, marginTop: space.roomy },
  figure: { flexShrink: 1 },
  figureValue: {
    ...type.display,
    fontFamily: family.display,
    color: colour.accent,
  },
  figureValueSmall: { ...type.title, fontFamily: family.bodySemibold },
  figureLabel: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: 2,
  },
  progressBlock: { marginTop: space.roomy },
  track: {
    height: 6,
    borderRadius: radius.pill,
    backgroundColor: colour.border,
    overflow: "hidden",
  },
  fill: { height: "100%", backgroundColor: colour.accent },
  progressText: {
    ...type.small,
    fontFamily: family.bodyMedium,
    color: colour.ink,
    marginTop: space.snug,
  },
  section: {
    marginTop: space.section,
    borderTopWidth: 1,
    borderTopColor: colour.border,
    paddingTop: space.roomy,
  },
  sectionLabel: {
    ...type.overline,
    fontFamily: family.bodyMedium,
    color: colour.inkFaint,
    marginBottom: space.base,
  },
  muted: { ...type.small, fontFamily: family.body, color: colour.inkMuted },
  level: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.base,
    borderWidth: 1.5,
    borderColor: colour.border,
    borderRadius: radius.md,
    paddingHorizontal: space.comfortable,
    paddingVertical: space.base,
    marginBottom: space.snug,
  },
  levelReached: { borderColor: colour.accent, backgroundColor: colour.accentSubtle },
  levelText: { flex: 1 },
  levelName: { ...type.body, fontFamily: family.bodySemibold, color: colour.ink },
  levelNameReached: { color: colour.accentPressed },
  levelPoints: {
    ...type.body,
    fontFamily: family.bodySemibold,
    color: colour.inkMuted,
  },
  shield: {
    ...type.title,
    fontFamily: family.bodySemibold,
    color: colour.ink,
    marginBottom: space.tight,
    textTransform: "capitalize",
  },
});
