import { useMutation, useQuery } from "@tanstack/react-query";
import * as Location from "expo-location";
import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Animated, { FadeIn } from "react-native-reanimated";
import Svg, { Circle, Path } from "react-native-svg";

import { Dropdown, type Option } from "@/components/dropdown";
import { duration } from "@/design/motion";
import { confirm, reject } from "@/design/risk";
import { MINIMUM_TARGET, colour, family, radius, space, type } from "@/design/tokens";
import { api } from "@/lib/api/client";
import type { PublicDistrict } from "@/lib/api/types";

/**
 * Beyond this, the nearest district centre is far enough away that we should say so
 * plainly rather than quietly assume it.
 */
const CONFIDENT_MATCH_KM = 12;

/**
 * Where you live.
 *
 * What the platform stores is always a **district**, because that is the resolution the
 * engine forecasts at. Region is only a way of narrowing 260 districts to a dozen.
 *
 * Two routes, and the fast one comes first: let the phone say where it is, or pick region
 * then district. Location matching uses district centres rather than boundaries, so it can
 * land on a neighbour; the match is always shown with its distance and can be changed,
 * rather than being applied silently.
 */
export function WhereYouLive({
  districtId,
  onChange,
}: {
  districtId: string | null;
  onChange: (districtId: string) => void;
}) {
  const [region, setRegion] = useState<string | null>(null);
  const [locatedNote, setLocatedNote] = useState<string | null>(null);
  const [locationDenied, setLocationDenied] = useState(false);

  const districts = useQuery({
    queryKey: ["public-districts"],
    queryFn: () => api.publicDistricts(),
  });

  const all = useMemo(() => districts.data ?? [], [districts.data]);

  const regions = useMemo<Option[]>(() => {
    const names = [...new Set(all.map((district) => district.region))].sort();
    return names.map((name) => ({
      value: name,
      label: name,
      detail: `${all.filter((district) => district.region === name).length} districts`,
    }));
  }, [all]);

  const districtsInRegion = useMemo<Option[]>(
    () =>
      all
        .filter((district) => district.region === region)
        .sort((first, second) => first.name.localeCompare(second.name))
        .map((district) => ({ value: district.district_id, label: district.name })),
    [all, region],
  );

  const chosen = all.find((district) => district.district_id === districtId) ?? null;

  const locate = useMutation({
    mutationFn: async () => {
      const permission = await Location.requestForegroundPermissionsAsync();
      if (!permission.granted) throw new Error("denied");

      const position = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      return api.nearestDistrict(position.coords.latitude, position.coords.longitude);
    },
    onSuccess: async (nearest) => {
      applyDistrict(nearest.district);
      setLocatedNote(
        nearest.distance_km <= CONFIDENT_MATCH_KM
          ? `Matched from your location, ${nearest.distance_km} km from the district centre.`
          : `Closest match is ${nearest.distance_km} km away. Check it is right.`,
      );
      await confirm();
    },
    onError: async (error) => {
      if (error instanceof Error && error.message === "denied") setLocationDenied(true);
      await reject();
    },
  });

  const applyDistrict = (district: PublicDistrict) => {
    setRegion(district.region);
    onChange(district.district_id);
  };

  return (
    <View>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Use my location to find my district"
        accessibilityHint="Asks permission, then matches your position to a district"
        onPress={() => {
          setLocatedNote(null);
          locate.mutate();
        }}
        disabled={locate.isPending}
        style={styles.locate}
      >
        <Pin />
        <Text style={styles.locateText}>
          {locate.isPending ? "Finding your district…" : "Use my location"}
        </Text>
      </Pressable>

      {locationDenied ? (
        <Text style={styles.note}>
          Location is off, which is fine. Choose your region and district below.
        </Text>
      ) : null}

      {locate.isError && !locationDenied ? (
        <Text style={styles.note}>
          That did not work. Choose your region and district below.
        </Text>
      ) : null}

      <View style={styles.divider}>
        <View style={styles.rule} />
        <Text style={styles.dividerText}>or choose it</Text>
        <View style={styles.rule} />
      </View>

      <Dropdown
        label="Region"
        placeholder={
          districts.isPending
            ? "Loading regions…"
            : districts.isError
              ? "Could not load regions"
              : "Choose your region"
        }
        options={regions}
        loading={districts.isPending}
        error={
          districts.isError
            ? "The list of districts could not be loaded. Check your connection."
            : null
        }
        onRetry={() => void districts.refetch()}
        value={region}
        onChange={(next) => {
          setRegion(next);
          // The old district belongs to the old region, so it cannot stand.
          if (chosen !== null && chosen.region !== next) onChange("");
          setLocatedNote(null);
        }}
      />

      <View style={styles.gap} />

      <Dropdown
        label="District"
        placeholder={region === null ? "Choose a region first" : "Choose your district"}
        searchPlaceholder="Search districts"
        options={districtsInRegion}
        loading={districts.isPending}
        error={
          districts.isError
            ? "The list of districts could not be loaded. Check your connection."
            : null
        }
        onRetry={() => void districts.refetch()}
        emptyMessage="No districts listed for this region."
        value={districtId}
        onChange={(next) => {
          onChange(next);
          setLocatedNote(null);
        }}
        disabled={region === null}
      />

      {locatedNote !== null ? (
        <Animated.Text
          entering={FadeIn.duration(duration.medium)}
          style={styles.matched}
        >
          {locatedNote}
        </Animated.Text>
      ) : null}
    </View>
  );
}

function Pin() {
  return (
    <Svg width={20} height={20} viewBox="0 0 24 24" fill="none">
      <Path
        d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z"
        stroke={colour.accent}
        strokeWidth={2}
        strokeLinejoin="round"
      />
      <Circle cx={12} cy={10} r={2.6} stroke={colour.accent} strokeWidth={2} />
    </Svg>
  );
}

const styles = StyleSheet.create({
  locate: {
    minHeight: MINIMUM_TARGET + 6,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: space.snug,
    borderWidth: 1.5,
    borderColor: colour.accent,
    borderRadius: radius.md,
    paddingVertical: space.base,
  },
  locateText: {
    ...type.body,
    fontFamily: family.bodySemibold,
    color: colour.accent,
  },
  note: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.inkMuted,
    marginTop: space.snug,
  },
  divider: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.base,
    marginVertical: space.roomy,
  },
  rule: { flex: 1, height: 1, backgroundColor: colour.border },
  dividerText: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.inkFaint,
  },
  gap: { height: space.base },
  matched: {
    ...type.caption,
    fontFamily: family.body,
    color: colour.accentPressed,
    marginTop: space.base,
  },
});
