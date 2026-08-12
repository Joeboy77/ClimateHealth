import { useMutation } from "@tanstack/react-query";
import { Image } from "expo-image";
import * as ImagePicker from "expo-image-picker";
import * as Location from "expo-location";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
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
import Animated, { FadeIn, FadeInDown } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Circle, Path } from "react-native-svg";

import { duration, staggerDelay } from "@/design/motion";
import { confirm, reject, tick } from "@/design/risk";
import {
  MINIMUM_TARGET,
  colour,
  elevation,
  family,
  radius,
  space,
  type,
} from "@/design/tokens";
import { HAZARDS } from "@/features/report/hazards";
import { api, uploadReportPhoto } from "@/lib/api/client";
import { enqueue } from "@/lib/offline/report-queue";
import type { ReportType } from "@/lib/api/types";
import { useSession } from "@/lib/identity/session";

const NOTE_LIMIT = 300;

/**
 * Community Watch.
 *
 * A citizen is a sensor here, not a suggestion box: a verified report of standing water
 * raises the district's malaria score the same way a rain gauge would. The screen says so
 * after submitting, because an app that swallows a report without explaining what becomes
 * of it teaches people to stop sending them.
 *
 * The photograph is uploaded before the report so a weak connection retries the bytes
 * rather than the whole submission, and a report can be filed without one.
 */
export default function ReportScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { loading, token, citizen } = useSession();

  // A report belongs to a Guardian and a district, so there is nothing to submit without
  // one. Same guard as Today, rather than letting the send fail at the last step.
  useEffect(() => {
    if (!loading && token === null) router.replace("/join");
  }, [loading, token, router]);

  const [hazard, setHazard] = useState<ReportType | null>(null);
  const [note, setNote] = useState("");
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [coordinates, setCoordinates] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);
  const [outcome, setOutcome] = useState<"sent" | "held" | null>(null);

  const attach = async (fromCamera: boolean) => {
    await tick();
    const permission = fromCamera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) return;

    const result = fromCamera
      ? await ImagePicker.launchCameraAsync({ quality: 0.6 })
      : await ImagePicker.launchImageLibraryAsync({ quality: 0.6 });

    const asset = result.canceled ? null : result.assets[0];
    if (asset) setPhotoUri(asset.uri);
  };

  const locate = async () => {
    await tick();
    const permission = await Location.requestForegroundPermissionsAsync();
    if (!permission.granted) return;
    const position = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.Balanced,
    });
    setCoordinates({
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
    });
  };

  const send = useMutation({
    mutationFn: async () => {
      if (token === null || citizen === null) throw new Error("Not signed in");

      const draft = {
        districtId: citizen.district_id,
        reportType: hazard ?? "stagnant_water",
        note: note.trim() || "Reported from Dawuro",
        photoUri,
        latitude: coordinates?.latitude ?? null,
        longitude: coordinates?.longitude ?? null,
      };

      try {
        const photoReference =
          photoUri === null ? null : await uploadReportPhoto(token, photoUri);

        await api.submitReport(token, {
          district_id: draft.districtId,
          report_type: draft.reportType,
          note: draft.note,
          photo_reference: photoReference,
          latitude: draft.latitude,
          longitude: draft.longitude,
        });
        return "sent" as const;
      } catch {
        // Held rather than lost. The people most exposed to climate risk have the least
        // reliable connectivity, and a report that vanishes teaches them not to bother.
        enqueue(draft);
        return "held" as const;
      }
    },
    onSuccess: async (result) => {
      await confirm();
      setOutcome(result);
    },
    onError: async () => {
      await reject();
    },
  });

  if (outcome !== null) {
    return <Finished outcome={outcome} onDone={() => router.replace("/")} />;
  }

  return (
    <KeyboardAvoidingView
      style={styles.host}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        contentContainerStyle={[
          styles.content,
          { paddingTop: insets.top + space.roomy, paddingBottom: space.section },
        ]}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>What have you seen?</Text>
        <Text style={styles.aside}>
          Reports go to your district health officer. Once verified, they change what
          the engine expects here.
        </Text>

        <View style={styles.grid}>
          {HAZARDS.map((entry, index) => (
            <Animated.View
              key={entry.type}
              entering={FadeInDown.delay(staggerDelay(index)).duration(duration.medium)}
              style={styles.gridItem}
            >
              <Pressable
                accessibilityRole="radio"
                accessibilityState={{ selected: hazard === entry.type }}
                accessibilityLabel={`${entry.label}. ${entry.help}`}
                onPress={() => {
                  void tick();
                  setHazard(entry.type);
                }}
                style={[styles.hazard, hazard === entry.type && styles.hazardOn]}
              >
                <Text
                  style={[
                    styles.hazardLabel,
                    hazard === entry.type && styles.hazardLabelOn,
                  ]}
                >
                  {entry.label}
                </Text>
                <Text style={styles.hazardHelp}>{entry.help}</Text>
              </Pressable>
            </Animated.View>
          ))}
        </View>

        <Text style={styles.section}>Add a photo</Text>
        {photoUri === null ? (
          <View style={styles.row}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Take a photo"
              onPress={() => void attach(true)}
              style={styles.secondary}
            >
              <Camera />
              <Text style={styles.secondaryText}>Camera</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Choose a photo from your phone"
              onPress={() => void attach(false)}
              style={styles.secondary}
            >
              <Text style={styles.secondaryText}>From phone</Text>
            </Pressable>
          </View>
        ) : (
          <Animated.View entering={FadeIn.duration(duration.medium)}>
            <Image
              source={{ uri: photoUri }}
              style={styles.preview}
              contentFit="cover"
            />
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Remove this photo"
              onPress={() => setPhotoUri(null)}
              style={styles.remove}
            >
              <Text style={styles.removeText}>Remove photo</Text>
            </Pressable>
          </Animated.View>
        )}

        <Text style={styles.section}>Where is it?</Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={
            coordinates
              ? "Location attached. Tap to update it"
              : "Attach the exact location"
          }
          onPress={() => void locate()}
          style={styles.secondary}
        >
          <Pin />
          <Text style={styles.secondaryText}>
            {coordinates ? "Location attached" : "Use my exact location"}
          </Text>
        </Pressable>
        <Text style={styles.hint}>
          Optional, but it tells the officer which drain or which street.
        </Text>

        <Text style={styles.section}>Anything to add?</Text>
        <TextInput
          value={note}
          onChangeText={(next) => setNote(next.slice(0, NOTE_LIMIT))}
          placeholder="How long has it been there? How many people?"
          placeholderTextColor={colour.inkFaint}
          accessibilityLabel="A note about what you saw"
          multiline
          style={styles.note}
        />

        {send.isError ? (
          <Text style={styles.error}>Something went wrong. Try sending again.</Text>
        ) : null}
      </ScrollView>

      <View
        style={[styles.footer, { paddingBottom: insets.bottom + space.comfortable }]}
      >
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Send this report"
          accessibilityState={{ disabled: hazard === null || send.isPending }}
          disabled={hazard === null || send.isPending}
          onPress={() => send.mutate()}
          style={[
            styles.primary,
            (hazard === null || send.isPending) && styles.primaryOff,
          ]}
        >
          <Text style={styles.primaryText}>
            {send.isPending ? "Sending…" : "Send report"}
          </Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

/**
 * What happens next, said plainly. Most reporting screens end at "thanks", which teaches
 * people their report went nowhere.
 */
function Finished({
  outcome,
  onDone,
}: {
  outcome: "sent" | "held";
  onDone: () => void;
}) {
  const insets = useSafeAreaInsets();

  return (
    <View
      style={[styles.host, styles.sent, { paddingTop: insets.top + space.section }]}
    >
      <Animated.View entering={FadeIn.duration(duration.medium)}>
        <Text style={styles.title}>
          {outcome === "sent" ? "Report sent" : "Saved on your phone"}
        </Text>
        {outcome === "sent" ? (
          <>
            <Text style={styles.aside}>
              A health officer in your district will check it. Once it is verified it
              becomes a signal in the engine, so the risk score for your district
              reflects what you saw.
            </Text>
            <Text style={styles.aside}>
              You earn Guardian points when it is verified.
            </Text>
          </>
        ) : (
          <>
            <Text style={styles.aside}>
              There was no connection, so your report is being held here. Dawuro will
              send it by itself the next time you are online. You do not need to write
              it again.
            </Text>
            <Text style={styles.aside}>
              It reaches your district health officer once it is sent.
            </Text>
          </>
        )}
      </Animated.View>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Back to today"
        onPress={onDone}
        style={[styles.primary, styles.sentButton]}
      >
        <Text style={styles.primaryText}>Back to today</Text>
      </Pressable>
    </View>
  );
}

function Camera() {
  return (
    <Svg width={18} height={18} viewBox="0 0 24 24" fill="none">
      <Path
        d="M3 8.5A2.5 2.5 0 0 1 5.5 6h1.6l1-2h7.8l1 2h1.6A2.5 2.5 0 0 1 21 8.5v9A2.5 2.5 0 0 1 18.5 20h-13A2.5 2.5 0 0 1 3 17.5v-9Z"
        stroke={colour.accent}
        strokeWidth={1.8}
        strokeLinejoin="round"
      />
      <Circle cx={12} cy={13} r={3.4} stroke={colour.accent} strokeWidth={1.8} />
    </Svg>
  );
}

function Pin() {
  return (
    <Svg width={18} height={18} viewBox="0 0 24 24" fill="none">
      <Path
        d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z"
        stroke={colour.accent}
        strokeWidth={1.8}
        strokeLinejoin="round"
      />
      <Circle cx={12} cy={10} r={2.4} stroke={colour.accent} strokeWidth={1.8} />
    </Svg>
  );
}

const styles = StyleSheet.create({
  host: { flex: 1, backgroundColor: colour.canvas },
  content: { paddingHorizontal: space.comfortable },
  sent: { paddingHorizontal: space.comfortable, justifyContent: "space-between" },
  sentButton: { marginBottom: space.section },
  title: { ...type.display, fontFamily: family.display, color: colour.ink },
  aside: {
    ...type.body,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: space.base,
  },
  section: {
    ...type.overline,
    fontFamily: family.bodyMedium,
    color: colour.inkFaint,
    textTransform: "uppercase",
    marginTop: space.generous,
    marginBottom: space.base,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: space.snug,
    marginTop: space.roomy,
  },
  gridItem: { width: "48.5%" },
  hazard: {
    minHeight: 88,
    justifyContent: "center",
    backgroundColor: colour.surface,
    borderWidth: 1.5,
    borderColor: colour.border,
    borderRadius: radius.md,
    padding: space.base,
  },
  hazardOn: { borderColor: colour.accent, backgroundColor: colour.accentSubtle },
  hazardLabel: { ...type.body, fontFamily: family.bodySemibold, color: colour.ink },
  hazardLabelOn: { color: colour.accentPressed },
  hazardHelp: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: 2,
  },
  row: { flexDirection: "row", gap: space.snug },
  secondary: {
    minHeight: MINIMUM_TARGET,
    flexGrow: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: space.snug,
    borderWidth: 1.5,
    borderColor: colour.accent,
    borderRadius: radius.md,
    paddingHorizontal: space.comfortable,
  },
  secondaryText: {
    ...type.body,
    fontFamily: family.bodySemibold,
    color: colour.accent,
  },
  preview: {
    width: "100%",
    height: 190,
    borderRadius: radius.md,
    backgroundColor: colour.raised,
  },
  remove: { minHeight: MINIMUM_TARGET, justifyContent: "center" },
  removeText: { ...type.small, fontFamily: family.bodyMedium, color: colour.inkMuted },
  hint: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: space.snug,
  },
  note: {
    ...type.body,
    fontFamily: family.body,
    color: colour.ink,
    minHeight: 96,
    textAlignVertical: "top",
    backgroundColor: colour.surface,
    borderWidth: 1.5,
    borderColor: colour.border,
    borderRadius: radius.md,
    padding: space.base,
  },
  error: {
    ...type.small,
    fontFamily: family.body,
    color: colour.riskSevere,
    marginTop: space.base,
  },
  footer: {
    paddingHorizontal: space.comfortable,
    paddingTop: space.base,
    borderTopWidth: 1,
    borderTopColor: colour.border,
  },
  primary: {
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
