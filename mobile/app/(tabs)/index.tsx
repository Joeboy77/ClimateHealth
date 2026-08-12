import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  Text,
  View,
} from "react-native";
import Animated, { FadeIn, FadeInDown } from "react-native-reanimated";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { ListenButton } from "@/components/listen-button";
import { ClimateStrip } from "@/components/climate-strip";
import { GuardianBar } from "@/components/guardian-bar";
import { PressableCard } from "@/components/pressable-card";
import { RiskDial, RISK_DIAL_SIZE } from "@/components/risk-dial";
import { duration, staggerDelay } from "@/design/motion";
import { RISK, tick, vibrateForLevel } from "@/design/risk";
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
import { savedAgo, savedForecast, saveForecast } from "@/lib/offline/forecast-cache";
import { flush, queuedCount } from "@/lib/offline/report-queue";
import {
  conditionLabel,
  type Forecast,
  type LagWindow,
  type RiskLevel,
} from "@/lib/api/types";

/**
 * Today: the whole product in one screen.
 *
 * A Guardian who has not joined yet is sent to sign up; everybody else lands straight on
 * their district's forecast, because the point of Dawuro is that opening it is the entire
 * interaction.
 */
export default function TodayScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { loading, token, citizen } = useSession();

  useEffect(() => {
    if (!loading && token === null) router.replace("/join");
  }, [loading, token, router]);

  const districtId = citizen?.district_id ?? "";
  const [held, setHeld] = useState(queuedCount());

  // Anything written without signal sends itself when the app next opens with a working
  // connection. Nobody has to remember to retry, which is the point of holding it.
  useEffect(() => {
    if (token === null) return;
    void flush(token).then((result) => setHeld(result.remaining));
  }, [token]);

  const forecast = useQuery({
    queryKey: ["forecast", districtId, citizen?.language],
    queryFn: async () => {
      const fetched = await api.forecast(token ?? "", districtId, citizen?.language);
      saveForecast(districtId, fetched);
      return fetched;
    },
    enabled: token !== null && districtId !== "",
  });

  const guardian = useQuery({
    queryKey: ["guardian", citizen?.user_id],
    queryFn: () => api.guardian(token ?? "", citizen?.user_id ?? ""),
    enabled: token !== null && (citizen?.user_id ?? "") !== "",
  });

  // What we last knew, for when the network is gone.
  const saved = useMemo(
    () => (districtId === "" ? null : savedForecast(districtId)),
    [districtId],
  );

  const level = forecast.data?.top_risks[0]?.level;

  useEffect(() => {
    if (level !== undefined) void vibrateForLevel(level);
  }, [level]);

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colour.canvas }}
      contentContainerStyle={{
        paddingTop: insets.top + space.roomy,
        paddingBottom: insets.bottom + space.section,
        paddingHorizontal: space.comfortable,
      }}
      refreshControl={
        <RefreshControl
          refreshing={forecast.isRefetching}
          onRefresh={() => void forecast.refetch()}
          tintColor={colour.inkMuted}
          accessibilityLabel="Pull down to check for a newer forecast"
        />
      }
    >
      {guardian.data ? (
        <GuardianBar
          points={guardian.data.points}
          streakDays={guardian.data.streak.current_days}
          levelName={guardian.data.level.name}
        />
      ) : null}

      {held > 0 ? <Held count={held} /> : null}

      {forecast.data ? (
        <Today
          forecast={forecast.data}
          level={level ?? "low"}
          voiceFirst={citizen?.tier === "voice_first"}
        />
      ) : forecast.isError && saved !== null ? (
        <>
          <SavedNotice savedAt={saved.savedAt} />
          <Today
            forecast={saved.forecast}
            level={saved.forecast.top_risks[0]?.level ?? "low"}
            voiceFirst={citizen?.tier === "voice_first"}
          />
        </>
      ) : forecast.isError ? (
        <Unavailable />
      ) : (
        <Waiting />
      )}
    </ScrollView>
  );
}

function Today({
  forecast,
  level,
  voiceFirst,
}: {
  forecast: Forecast;
  level: RiskLevel;
  voiceFirst: boolean;
}) {
  const router = useRouter();
  const presentation = RISK[level];
  const [showingReasons, setShowingReasons] = useState(false);
  const reasons = forecast.top_risks[0]?.reasons ?? [];

  return (
    <View>
      <Animated.View entering={FadeIn.duration(duration.short)}>
        <Text
          style={{
            ...type.overline,
            color: colour.inkFaint,
            textTransform: "uppercase",
          }}
        >
          Today in
        </Text>
        <Text
          style={{ ...type.title, fontFamily: family.bodySemibold, color: colour.ink }}
        >
          {forecast.district_name}
        </Text>
      </Animated.View>

      {/* One accessible summary for the whole hero: a screen-reader user should hear the
          verdict as a sentence, not as four disconnected fragments. */}
      <View
        accessible
        accessibilityRole="summary"
        accessibilityLabel={`${presentation.plain}. ${forecast.headline}. ${forecast.summary}`}
        style={{ alignItems: "center", marginTop: space.roomy }}
      >
        <View style={{ height: RISK_DIAL_SIZE, justifyContent: "center" }}>
          <RiskDial level={level} />
          <View
            style={{
              position: "absolute",
              width: RISK_DIAL_SIZE,
              alignItems: "center",
            }}
          >
            <Text
              style={{
                ...type.verdict,
                fontFamily: family.display,
                color: presentation.colour,
              }}
            >
              {presentation.label}
            </Text>
            <Text
              style={{ ...type.small, color: colour.inkMuted, marginTop: space.tight }}
            >
              {conditionLabel(forecast.top_risks[0]?.condition ?? "")} risk
            </Text>
          </View>
        </View>

        <Text
          style={{
            ...type.display,
            fontFamily: family.display,
            color: colour.ink,
            textAlign: "center",
            marginTop: space.roomy,
          }}
        >
          {forecast.headline}
        </Text>
        <Text
          // Centred display type reads as a headline; centred body copy just makes the
          // eye hunt for each line start. The verdict stays centred, the explanation
          // does not.
          style={{
            ...type.body,
            fontFamily: family.body,
            color: colour.inkMuted,
            marginTop: space.base,
          }}
        >
          {forecast.summary}
        </Text>
      </View>

      {/* The whole warning, in the order somebody would want to hear it. Placed directly
          under the verdict for a Voice-First Guardian, who is the reason it exists. */}
      <View
        style={{
          marginTop: space.roomy,
          alignItems: voiceFirst ? "stretch" : "flex-start",
        }}
      >
        <ListenButton
          language={forecast.language}
          prominent={voiceFirst}
          parts={[
            { text: forecast.headline, language: forecast.language },
            { text: forecast.summary, language: forecast.language },
            { text: forecast.action_today, language: forecast.language },
          ]}
        />
      </View>

      {forecast.wording === "curated_unreviewed" ? (
        <Text
          style={{
            ...type.caption,
            fontFamily: family.body,
            color: colour.inkFaint,
            marginTop: space.base,
          }}
        >
          This Twi wording is awaiting review by a Twi speaker.
        </Text>
      ) : null}

      <Animated.View
        entering={FadeInDown.delay(staggerDelay(1)).duration(duration.medium)}
      >
        <PressableCard
          onPress={() => {
            void tick();
            setShowingReasons((open) => !open);
          }}
          accessibilityLabel={`Today's action: ${forecast.action_today}`}
          accessibilityHint={
            showingReasons
              ? "Hides the reasons behind this warning"
              : "Shows the reasons behind this warning"
          }
          accessibilityState={{ expanded: showingReasons }}
          style={{
            marginTop: space.generous,
            backgroundColor: colour.surface,
            borderRadius: radius.lg,
            borderLeftWidth: 4,
            borderLeftColor: presentation.colour,
            padding: space.comfortable,
            ...elevation.resting,
          }}
        >
          <Text
            style={{
              ...type.overline,
              color: colour.inkFaint,
              textTransform: "uppercase",
            }}
          >
            Do this today
          </Text>
          <Text
            style={{
              ...type.heading,
              fontFamily: family.bodyMedium,
              color: colour.ink,
              marginTop: space.snug,
            }}
          >
            {forecast.action_today}
          </Text>

          {reasons.length > 0 ? (
            <Text
              style={{
                ...type.caption,
                fontFamily: family.bodyMedium,
                color: colour.accent,
                marginTop: space.base,
              }}
            >
              {showingReasons ? "Hide why" : "Why this warning?"}
            </Text>
          ) : null}

          {showingReasons ? (
            <Animated.View
              entering={FadeIn.duration(duration.short)}
              style={{ marginTop: space.base }}
            >
              {/* The engine's own reasons, unedited. This is the difference between a
                  warning somebody trusts and one they scroll past. */}
              {reasons.map((reason) => (
                <Text
                  key={reason}
                  style={{
                    ...type.small,
                    fontFamily: family.body,
                    color: colour.inkMuted,
                    marginTop: space.tight,
                  }}
                >
                  · {reason}
                </Text>
              ))}
            </Animated.View>
          ) : null}
        </PressableCard>
      </Animated.View>

      {forecast.top_risks.length > 1 ? (
        <View style={{ marginTop: space.generous }}>
          <Text
            style={{
              ...type.overline,
              color: colour.inkFaint,
              textTransform: "uppercase",
            }}
          >
            Also rising here
          </Text>
          {forecast.top_risks.slice(1, 4).map((risk, index) => (
            <Animated.View
              key={risk.condition}
              entering={FadeInDown.delay(staggerDelay(index + 2)).duration(
                duration.medium,
              )}
            >
              <View
                accessible
                accessibilityRole="text"
                accessibilityLabel={`${conditionLabel(risk.condition)}, ${risk.level} risk, cases expected in ${onsetText(risk.lag_window)}`}
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  gap: space.base,
                  paddingVertical: space.base,
                  borderBottomWidth: 1,
                  borderBottomColor: colour.border,
                }}
              >
                <View
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: radius.pill,
                    backgroundColor: RISK[risk.level].colour,
                  }}
                />
                <Text
                  style={{
                    ...type.body,
                    fontFamily: family.body,
                    color: colour.ink,
                    flex: 1,
                  }}
                >
                  {conditionLabel(risk.condition)}
                </Text>
                <Text
                  style={{
                    ...type.caption,
                    fontFamily: family.body,
                    color: colour.inkMuted,
                  }}
                >
                  {onsetText(risk.lag_window)}
                </Text>
              </View>
            </Animated.View>
          ))}
        </View>
      ) : null}

      <ClimateStrip climate={forecast.climate} />

      <Pressable
        onPress={() => {
          void tick();
          router.push("/district");
        }}
        accessibilityRole="button"
        accessibilityLabel="Open your district: shield, agency progress, everything watched"
        style={{
          marginTop: space.generous,
          minHeight: MINIMUM_TARGET,
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "space-between",
          borderTopWidth: 1,
          borderTopColor: colour.border,
          paddingTop: space.comfortable,
        }}
      >
        <View>
          <Text
            style={{ ...type.body, fontFamily: family.bodySemibold, color: colour.ink }}
          >
            Your district
          </Text>
          <Text
            style={{
              ...type.caption,
              fontFamily: family.body,
              color: colour.inkMuted,
              marginTop: 2,
            }}
          >
            Shield, agency progress, everything watched
          </Text>
        </View>
        <Text
          style={{
            ...type.body,
            fontFamily: family.bodySemibold,
            color: colour.accent,
          }}
        >
          Open
        </Text>
      </Pressable>
    </View>
  );
}

/** Days for the fast pathways, weeks for the slow ones: the way a person would say it. */
function onsetText(window: LagWindow): string {
  if (window.maximum_days <= 14) {
    return `${window.minimum_days}\u2013${window.maximum_days} days`;
  }
  const minimumWeeks = Math.floor(window.minimum_days / 7);
  const maximumWeeks = Math.floor(window.maximum_days / 7);
  if (minimumWeeks === 0) return `under ${maximumWeeks} weeks`;
  return `${minimumWeeks}\u2013${maximumWeeks} weeks`;
}

/** Shown above a forecast we could not refresh, so nobody mistakes it for today's. */
function SavedNotice({ savedAt }: { savedAt: string }) {
  return (
    <View
      accessible
      accessibilityRole="text"
      accessibilityLabel={`This forecast was saved ${savedAgo(savedAt)}. It is not today's.`}
      style={{
        borderRadius: radius.md,
        borderWidth: 1.5,
        borderColor: colour.riskModerate,
        paddingHorizontal: space.comfortable,
        paddingVertical: space.base,
        marginBottom: space.base,
      }}
    >
      <Text
        style={{ ...type.small, fontFamily: family.bodySemibold, color: colour.ink }}
      >
        Saved forecast, from {savedAgo(savedAt)}
      </Text>
      <Text
        style={{
          ...type.caption,
          fontFamily: family.body,
          color: colour.inkMuted,
          marginTop: 2,
        }}
      >
        No connection, so this is what Dawuro last knew. Pull down to try again.
      </Text>
    </View>
  );
}

/** Reports written without a connection, still waiting their turn. */
function Held({ count }: { count: number }) {
  return (
    <View
      accessible
      accessibilityRole="text"
      accessibilityLabel={`${count} ${count === 1 ? "report is" : "reports are"} saved on this phone and will send when you are online`}
      style={{
        marginTop: space.base,
        borderRadius: radius.md,
        borderWidth: 1.5,
        borderColor: colour.border,
        paddingHorizontal: space.comfortable,
        paddingVertical: space.base,
      }}
    >
      <Text style={{ ...type.small, fontFamily: family.bodyMedium, color: colour.ink }}>
        {count === 1 ? "1 report waiting to send" : `${count} reports waiting to send`}
      </Text>
      <Text
        style={{
          ...type.caption,
          fontFamily: family.body,
          color: colour.inkMuted,
          marginTop: 2,
        }}
      >
        Saved on this phone. They will send by themselves when you are online.
      </Text>
    </View>
  );
}

function Waiting() {
  return (
    <View style={{ paddingTop: space.section, alignItems: "center" }}>
      <ActivityIndicator color={colour.accent} />
      <Text
        style={{ ...type.small, color: colour.inkMuted, marginTop: space.comfortable }}
      >
        Reading today&rsquo;s conditions
      </Text>
    </View>
  );
}

function Unavailable() {
  return (
    <View style={{ paddingTop: space.section }}>
      <Text style={{ ...type.title, fontFamily: family.display, color: colour.ink }}>
        Today&rsquo;s forecast is not available
      </Text>
      <Text
        style={{
          ...type.body,
          fontFamily: family.body,
          color: colour.inkMuted,
          marginTop: space.base,
        }}
      >
        The service could not be reached. Your last saved forecast will appear here once
        offline storage is in place.
      </Text>
    </View>
  );
}
