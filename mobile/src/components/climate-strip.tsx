import { StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Path } from "react-native-svg";

import { colour, family, radius, space, type } from "@/design/tokens";
import type { ClimateSnapshot } from "@/lib/api/types";

/**
 * Today's weather, under today's warning.
 *
 * The health verdict is drawn from these four readings, and a person wants to know
 * whether it will rain as well as what the rain will do to them. Sending them to a
 * second app for half of that is how they stop opening this one.
 *
 * Every reading carries a plain-language word beside the number, because "42mm" tells
 * most people nothing and "heavy rain" tells them everything.
 */
export function ClimateStrip({ climate }: { climate: ClimateSnapshot }) {
  const dust = climate.dust_concentration_ug_m3 ?? climate.particulate_matter_10_ug_m3;

  return (
    <View style={styles.host}>
      <Text style={styles.heading}>CONDITIONS TODAY</Text>
      <View style={styles.row}>
        <Reading
          icon={<RainIcon />}
          value={`${Math.round(climate.rainfall_7d_mm)}`}
          unit="mm"
          label={rainWord(climate.rainfall_7d_mm)}
          caption="past 7 days"
        />
        <Reading
          icon={<HeatIcon />}
          value={`${Math.round(climate.temperature_max_c)}`}
          unit="°C"
          label={heatWord(climate.temperature_max_c)}
          caption="today's high"
        />
        <Reading
          icon={<HumidityIcon />}
          value={`${Math.round(climate.humidity_mean_percent)}`}
          unit="%"
          label={humidityWord(climate.humidity_mean_percent)}
          caption="humidity"
        />
        <Reading
          icon={<DustIcon />}
          value={dust === null ? "—" : `${Math.round(dust)}`}
          unit={dust === null ? "" : "µg"}
          label={dust === null ? "no reading" : dustWord(dust)}
          caption="dust in the air"
        />
      </View>
    </View>
  );
}

function Reading({
  icon,
  value,
  unit,
  label,
  caption,
}: {
  icon: React.ReactNode;
  value: string;
  unit: string;
  label: string;
  caption: string;
}) {
  return (
    <View
      style={styles.reading}
      accessible
      accessibilityLabel={`${caption}: ${value}${unit}, ${label}`}
    >
      {icon}
      <Text style={styles.value}>
        {value}
        <Text style={styles.unit}>{unit}</Text>
      </Text>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.caption}>{caption}</Text>
    </View>
  );
}

function rainWord(mm: number): string {
  if (mm < 5) return "dry week";
  if (mm < 20) return "light rain";
  if (mm < 50) return "steady rain";
  if (mm < 90) return "heavy rain";
  return "very heavy";
}

function heatWord(celsius: number): string {
  if (celsius < 28) return "mild";
  if (celsius < 33) return "warm";
  if (celsius < 38) return "hot";
  return "dangerous";
}

function humidityWord(percent: number): string {
  if (percent < 40) return "very dry";
  if (percent < 60) return "dry";
  if (percent < 75) return "humid";
  return "very humid";
}

function dustWord(value: number): string {
  if (value < 50) return "clear";
  if (value < 100) return "hazy";
  if (value < 200) return "dusty";
  return "harmful";
}

const ICON = 20;

function RainIcon() {
  return (
    <Svg width={ICON} height={ICON} viewBox="0 0 24 24">
      <Path
        d="M7 15a4 4 0 0 1 .6-7.96 5.5 5.5 0 0 1 10.5 1.5A3.5 3.5 0 0 1 17.5 15Z"
        fill={colour.accent}
        opacity={0.9}
      />
      <Path
        d="M9 18l-1 2.5M13 18l-1 2.5M17 18l-1 2.5"
        stroke={colour.accent}
        strokeWidth={1.8}
        strokeLinecap="round"
      />
    </Svg>
  );
}

function HeatIcon() {
  return (
    <Svg width={ICON} height={ICON} viewBox="0 0 24 24">
      <Circle cx={12} cy={12} r={4.2} fill={colour.riskHigh} />
      <Path
        d="M12 2.5v2.4M12 19.1v2.4M2.5 12h2.4M19.1 12h2.4M5.3 5.3l1.7 1.7M17 17l1.7 1.7M18.7 5.3L17 7M7 17l-1.7 1.7"
        stroke={colour.riskHigh}
        strokeWidth={1.8}
        strokeLinecap="round"
      />
    </Svg>
  );
}

function HumidityIcon() {
  return (
    <Svg width={ICON} height={ICON} viewBox="0 0 24 24">
      <Path
        d="M12 3.5c3.2 4 5.5 6.6 5.5 9.4a5.5 5.5 0 1 1-11 0c0-2.8 2.3-5.4 5.5-9.4Z"
        fill={colour.riskLow}
        opacity={0.9}
      />
    </Svg>
  );
}

function DustIcon() {
  return (
    <Svg width={ICON} height={ICON} viewBox="0 0 24 24">
      <Path
        d="M3.5 8.5h11M3.5 12.5h15M3.5 16.5h9"
        stroke={colour.riskModerate}
        strokeWidth={2}
        strokeLinecap="round"
      />
    </Svg>
  );
}

const styles = StyleSheet.create({
  host: { marginTop: space.section },
  heading: {
    ...type.overline,
    color: colour.inkFaint,
    textTransform: "uppercase",
    marginBottom: space.base,
  },
  row: {
    flexDirection: "row",
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colour.border,
    paddingVertical: space.comfortable,
  },
  reading: { flex: 1, alignItems: "center", gap: 3 },
  value: {
    ...type.title,
    fontFamily: family.display,
    color: colour.ink,
    marginTop: space.tight,
  },
  unit: { ...type.caption, fontFamily: family.body, color: colour.inkMuted },
  label: { ...type.caption, fontFamily: family.bodySemibold, color: colour.ink },
  caption: { ...type.overline, color: colour.inkFaint, fontSize: 9 },
});
