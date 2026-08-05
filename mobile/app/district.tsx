import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useEffect } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import Animated, { FadeIn } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { duration } from "@/design/motion";
import { RISK } from "@/design/risk";
import { colour, family, radius, space, type } from "@/design/tokens";
import { api } from "@/lib/api/client";
import { conditionLabel, type RiskLevel } from "@/lib/api/types";
import { useSession } from "@/lib/identity/session";

/**
 * Your district.
 *
 * The shield, what the district has actually done, and every risk the engine is tracking
 * rather than only the leading one. Proposal sections 11.2 and 19.2: the shield is
 * collective, so a person can see that their own reports and missions moved something
 * larger than their own score.
 */
export default function DistrictScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { loading, token, citizen } = useSession();

  useEffect(() => {
    if (!loading && token === null) router.replace("/join");
  }, [loading, token, router]);

  const districtId = citizen?.district_id ?? "";
  const ready = token !== null && districtId !== "";

  const shield = useQuery({
    queryKey: ["shield", districtId],
    queryFn: () => api.shield(token ?? "", districtId),
    enabled: ready,
  });

  const prevention = useQuery({
    queryKey: ["prevention", districtId],
    queryFn: () => api.preventionRecord(token ?? "", districtId),
    enabled: ready,
  });

  const risks = useQuery({
    queryKey: ["risks", districtId],
    queryFn: () => api.risk(token ?? "", districtId),
    enabled: ready,
  });

  const strength = shield.data?.strength ?? 0;

  return (
    <ScrollView
      style={styles.host}
      contentContainerStyle={[
        styles.content,
        { paddingTop: insets.top + space.roomy, paddingBottom: space.section },
      ]}
    >
      {shield.data ? (
        <Animated.View entering={FadeIn.duration(duration.medium)}>
          <Text style={styles.eyebrow}>YOUR DISTRICT</Text>
          <Text style={styles.name}>{shield.data.district_name}</Text>

          <View style={styles.shieldRow}>
            <Text style={styles.shieldStatus}>
              Shield {shield.data.status.replace(/_/g, " ")}
            </Text>
            <Text style={styles.shieldStrength}>{strength}/100</Text>
          </View>
          <View style={styles.track}>
            <View style={[styles.fill, { width: `${strength}%` }]} />
          </View>

          <Text style={styles.muted}>
            {shield.data.active_guardians} Guardians · {shield.data.community_reports}{" "}
            reports · {shield.data.missions_completed} missions
          </Text>

          {shield.data.outbreaks_averted > 0 ? (
            <View style={styles.averted}>
              <Text style={styles.avertedCount}>{shield.data.outbreaks_averted}</Text>
              <Text style={styles.avertedText}>
                {shield.data.outbreaks_averted === 1 ? "hazard" : "hazards"} where every
                agency finished its work before the cases were due
              </Text>
            </View>
          ) : null}
        </Animated.View>
      ) : (
        <Text style={styles.muted}>Loading your district…</Text>
      )}

      {prevention.data ? (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>WHAT THE AGENCIES DID</Text>
          <Text style={styles.standing}>
            {prevention.data.actions_on_time} of {prevention.data.actions_total} tasks
            closed before the cases were due
          </Text>
          {prevention.data.actions_overdue > 0 ? (
            <Text style={[styles.muted, styles.overdue]}>
              {prevention.data.actions_overdue} still overdue
            </Text>
          ) : (
            <Text style={styles.muted}>Nothing is overdue right now.</Text>
          )}
        </View>
      ) : null}

      {risks.data ? (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>EVERYTHING BEING WATCHED HERE</Text>
          {risks.data.risks.map((risk) => (
            <View key={risk.condition} style={styles.risk}>
              <View
                style={[
                  styles.dot,
                  { backgroundColor: RISK[risk.level as RiskLevel].colour },
                ]}
              />
              <Text style={styles.riskName}>{conditionLabel(risk.condition)}</Text>
              <Text style={styles.riskLevel}>
                {RISK[risk.level as RiskLevel].label}
              </Text>
            </View>
          ))}
          <Text style={styles.footnote}>
            Every condition the engine evaluated for this district today, not only the
            one at the top.
          </Text>
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
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
  shieldRow: {
    flexDirection: "row",
    alignItems: "baseline",
    justifyContent: "space-between",
    marginTop: space.roomy,
  },
  shieldStatus: {
    ...type.title,
    fontFamily: family.bodySemibold,
    color: colour.ink,
    textTransform: "capitalize",
  },
  shieldStrength: {
    ...type.body,
    fontFamily: family.bodySemibold,
    color: colour.accent,
  },
  track: {
    height: 8,
    borderRadius: radius.pill,
    backgroundColor: colour.border,
    overflow: "hidden",
    marginTop: space.snug,
    marginBottom: space.base,
  },
  fill: { height: "100%", backgroundColor: colour.accent },
  muted: { ...type.small, fontFamily: family.body, color: colour.inkMuted },
  overdue: { color: colour.riskHigh },
  averted: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.base,
    marginTop: space.roomy,
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: colour.riskLow,
    backgroundColor: colour.riskLowSurface,
    paddingHorizontal: space.comfortable,
    paddingVertical: space.base,
  },
  avertedCount: {
    ...type.display,
    fontFamily: family.display,
    color: colour.riskLow,
  },
  avertedText: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.ink,
    flex: 1,
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
  standing: {
    ...type.heading,
    fontFamily: family.bodyMedium,
    color: colour.ink,
    marginBottom: space.tight,
  },
  risk: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.base,
    paddingVertical: space.base,
    borderBottomWidth: 1,
    borderBottomColor: colour.border,
  },
  dot: { width: 8, height: 8, borderRadius: radius.pill },
  riskName: { ...type.body, fontFamily: family.body, color: colour.ink, flex: 1 },
  riskLevel: {
    ...type.small,
    fontFamily: family.bodyMedium,
    color: colour.inkMuted,
  },
  footnote: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.inkFaint,
    marginTop: space.base,
  },
});
