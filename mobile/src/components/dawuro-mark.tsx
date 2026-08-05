import Svg, { G, Path, type SvgProps } from "react-native-svg";

/**
 * The Dawuro mark.
 *
 * The dawuro is not a hand bell. It is the Akan double gong: two tapered iron bells of
 * unequal size joined by an arched yoke and struck with a wooden stick. Drawing the real
 * instrument gives a silhouette nothing else on a phone shares, which a generic bell
 * never would.
 *
 * Geometry rather than an image file, so it stays crisp at any size, takes its colour
 * from context, and can be animated part by part.
 */
export function DawuroMark({
  colour,
  size = 116,
  strikerRotation = 0,
  ...props
}: {
  colour: string;
  size?: number;
  /** Degrees the striker is drawn back. Driven by the opening's strike beat. */
  strikerRotation?: number;
} & SvgProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 120 120" fill="none" {...props}>
      {/* The yoke: one bent rod, with a bell hanging at each end. */}
      <Path
        d="M31 50C25 31 35 18 60 18s35 13 29 32"
        stroke={colour}
        strokeWidth={7}
        strokeLinecap="round"
      />

      {/* Larger bell, left: tapered body, flared mouth. */}
      <Path
        d="M31 45c4.5 0 8.2.8 8.7 2.7l7 43c.4 2.4-1.3 4.2-4.3 5.1-3.1 1-7.2 1.5-11.4 1.5s-8.3-.5-11.4-1.5c-3-.9-4.7-2.7-4.3-5.1l7-43C22.8 45.8 26.5 45 31 45Z"
        fill={colour}
      />

      {/* Smaller bell, right, hanging slightly higher. The pair is never symmetrical. */}
      <Path
        d="M89 53c3.8 0 6.9.7 7.3 2.2l5.8 35.6c.3 2-1.1 3.5-3.6 4.3-2.6.8-6 1.3-9.5 1.3s-6.9-.5-9.5-1.3c-2.5-.8-3.9-2.3-3.6-4.3l5.8-35.6C82.1 53.7 85.2 53 89 53Z"
        fill={colour}
      />

      {/* The striker, pivoting at the hand so it swings into the larger bell. */}
      <G transform={`rotate(${strikerRotation}, 96, 26)`}>
        <Path
          d="M96 26 49 61"
          stroke={colour}
          strokeWidth={7}
          strokeLinecap="round"
          opacity={0.9}
        />
      </G>
    </Svg>
  );
}
