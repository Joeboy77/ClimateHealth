import Svg, { Path } from "react-native-svg";

import { colour } from "@/design/tokens";

/** The streak mark, shared by the home bar and the quiz. */
export function Flame({
  size = 16,
  tint = colour.riskModerate,
}: {
  size?: number;
  tint?: string;
}) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <Path
        d="M12 2c1.5 3.5-1 5 .5 7.5C14 12 16 10 16 10s2 2.2 2 5a6 6 0 1 1-12 0c0-3.6 2.8-5.5 3.5-7.5C10.2 5.4 10 3.4 12 2Z"
        fill={tint}
      />
    </Svg>
  );
}
