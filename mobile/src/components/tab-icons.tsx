import Svg, { Circle, Path } from "react-native-svg";

/**
 * The tab marks.
 *
 * Drawn rather than pulled from an icon set, so they carry the same weight as the
 * dawuro mark and nothing looks borrowed. Each has a filled state for the tab you are
 * on, because colour alone should never be the thing that tells you where you are.
 */

export type TabIconProps = { colour: string; focused: boolean };

const SIZE = 26;
const STROKE = 1.9;

function line(focused: boolean, tint: string) {
  return {
    stroke: tint,
    strokeWidth: STROKE,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    fill: focused ? tint : "none",
    fillOpacity: focused ? 0.16 : 0,
  };
}

export function TodayIcon({ colour: tint, focused }: TabIconProps) {
  return (
    <Svg width={SIZE} height={SIZE} viewBox="0 0 24 24">
      <Path d="M4 11.5 12 4.5l8 7" {...line(false, tint)} />
      <Path
        d="M6 10.5V19a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-8.5"
        {...line(focused, tint)}
      />
    </Svg>
  );
}

export function LearnIcon({ colour: tint, focused }: TabIconProps) {
  return (
    <Svg width={SIZE} height={SIZE} viewBox="0 0 24 24">
      <Path d="M4 5.5h6a2 2 0 0 1 2 2V19a2 2 0 0 0-2-2H4Z" {...line(focused, tint)} />
      <Path d="M20 5.5h-6a2 2 0 0 0-2 2V19a2 2 0 0 1 2-2h6Z" {...line(focused, tint)} />
    </Svg>
  );
}

export function PlayIcon({ colour: tint, focused }: TabIconProps) {
  return (
    <Svg width={SIZE} height={SIZE} viewBox="0 0 24 24">
      <Circle cx={12} cy={12} r={8} {...line(focused, tint)} />
      <Path d="M9.5 12.3l1.8 1.8 3.4-3.9" {...line(false, tint)} />
    </Svg>
  );
}

export function ReportIcon({ colour: tint, focused }: TabIconProps) {
  return (
    <Svg width={SIZE} height={SIZE} viewBox="0 0 24 24">
      <Path
        d="M12 4.8 20 18.4a1 1 0 0 1-.87 1.5H4.87A1 1 0 0 1 4 18.4Z"
        {...line(focused, tint)}
      />
      <Path d="M12 10.4v3.6" {...line(false, tint)} />
      <Circle cx={12} cy={16.7} r={0.95} fill={tint} />
    </Svg>
  );
}

export function GuardianIcon({ colour: tint, focused }: TabIconProps) {
  return (
    <Svg width={SIZE} height={SIZE} viewBox="0 0 24 24">
      <Path
        d="M12 3.8 19 6.4v5.3c0 4-2.9 7.4-7 8.5-4.1-1.1-7-4.5-7-8.5V6.4Z"
        {...line(focused, tint)}
      />
      <Path d="M9 12.2l2 2 4-4.3" {...line(false, tint)} />
    </Svg>
  );
}
