import { useEffect } from "react";
import { Pressable, StyleSheet, Text, View, useWindowDimensions } from "react-native";
import Animated, {
  Easing,
  type SharedValue,
  cancelAnimation,
  runOnJS,
  useAnimatedProps,
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withDelay,
  withSequence,
  withSpring,
  withTiming,
} from "react-native-reanimated";
import Svg, { Circle, Defs, RadialGradient, Rect, Stop } from "react-native-svg";

import { DawuroMark } from "./dawuro-mark";
import { colour, family, space, type } from "@/design/tokens";

const AnimatedCircle = Animated.createAnimatedComponent(Circle);
const AnimatedDawuroMark = Animated.createAnimatedComponent(DawuroMark);

/**
 * The opening.
 *
 * The gong is struck three times. Each strike draws the striker back, snaps it through,
 * throws a ring outward and brightens the field for an instant, so the screen keeps time
 * rather than merely animating. On the last beat the dark field collapses into the bell
 * like an iris closing, and the day's forecast is already there behind it.
 *
 * One rule governs the whole thing: this is a warning application, so the opening may
 * never make somebody wait to read a warning. It runs *while* the forecast is being
 * fetched, and it is capped under two seconds. If the data arrives first the opening still
 * finishes its beat, because motion cut off halfway looks broken. If the data is slow the
 * opening ends anyway and the screen behind shows its own loading state. Under Reduce
 * Motion it is a still mark and a cross-fade.
 */

const STRIKE_AT_MS = [340, 800, 1260] as const;
const STRIKE_DRAW_MS = 150;
const RING_TRAVEL_MS = 1900;
const WORDMARK_AT_MS = 900;
const IRIS_AT_MS = 2250;
const IRIS_MS = 820;
const REDUCED_MOTION_HOLD_MS = 650;

const MARK_SIZE = 128;
const RING_START_RADIUS = 52;
/** Degrees the striker is drawn back before each strike. */
const STRIKER_DRAW = -26;

export function Opening({ onFinished }: { onFinished: () => void }) {
  const { width, height } = useWindowDimensions();
  const reduceMotion = useReducedMotion();

  const markOpacity = useSharedValue(0);
  const markScale = useSharedValue(reduceMotion ? 1 : 0.86);
  const striker = useSharedValue(0);
  const bloom = useSharedValue(0);
  const wordOpacity = useSharedValue(0);
  const iris = useSharedValue(0);
  const ringOne = useSharedValue(0);
  const ringTwo = useSharedValue(0);
  const ringThree = useSharedValue(0);
  const rings = [ringOne, ringTwo, ringThree];

  /** The opening is deliberately unhurried, so anybody in a hurry can cut it short. */
  const skip = () => {
    cancelAnimation(iris);
    iris.value = withTiming(1, { duration: 260 }, (done) => {
      if (done) runOnJS(onFinished)();
    });
  };

  /** A circle larger than the screen, shrinking into the bell. */
  const irisRadius = Math.hypot(width, height) / 2 + 40;
  const ringLimit = Math.hypot(width, height) * 0.55;

  useEffect(() => {
    markOpacity.value = withTiming(1, { duration: 380 });

    if (reduceMotion) {
      wordOpacity.value = withDelay(140, withTiming(1, { duration: 220 }));
      iris.value = withDelay(
        REDUCED_MOTION_HOLD_MS,
        withTiming(1, { duration: 260 }, (done) => {
          if (done) runOnJS(onFinished)();
        }),
      );
      return;
    }

    markScale.value = withSpring(1, { damping: 16, stiffness: 90, mass: 1.1 });
    wordOpacity.value = withDelay(
      WORDMARK_AT_MS,
      withTiming(1, { duration: 620, easing: Easing.out(Easing.cubic) }),
    );

    // Draw back, snap through, settle. The ring leaves on the snap, not on the draw,
    // so the sound and the movement agree.
    striker.value = withSequence(
      withDelay(
        STRIKE_AT_MS[0] - STRIKE_DRAW_MS,
        withTiming(STRIKER_DRAW, { duration: STRIKE_DRAW_MS }),
      ),
      withSpring(0, { damping: 11, stiffness: 300, mass: 0.7 }),
      withDelay(150, withTiming(STRIKER_DRAW, { duration: STRIKE_DRAW_MS })),
      withSpring(0, { damping: 11, stiffness: 300, mass: 0.7 }),
      withDelay(150, withTiming(STRIKER_DRAW, { duration: STRIKE_DRAW_MS })),
      withSpring(0, { damping: 11, stiffness: 300, mass: 0.7 }),
    );

    STRIKE_AT_MS.forEach((at, index) => {
      bloom.value = withDelay(
        at,
        withSequence(
          withTiming(1, { duration: 110 }),
          withTiming(0, { duration: 900, easing: Easing.out(Easing.quad) }),
        ),
      );

      const ring = rings[index];
      if (ring !== undefined) {
        ring.value = withDelay(
          at,
          withTiming(1, {
            duration: RING_TRAVEL_MS,
            easing: Easing.bezier(0.12, 0.7, 0.3, 1),
          }),
        );
      }
    });

    iris.value = withDelay(
      IRIS_AT_MS,
      withTiming(
        1,
        { duration: IRIS_MS, easing: Easing.bezier(0.7, 0, 0.3, 1) },
        (done) => {
          if (done) runOnJS(onFinished)();
        },
      ),
    );

    return () => {
      rings.forEach(cancelAnimation);
      cancelAnimation(striker);
      cancelAnimation(bloom);
      cancelAnimation(iris);
    };
    // The opening runs exactly once, on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const irisStyle = useAnimatedStyle(() => ({
    transform: [{ scale: 1 - iris.value }],
  }));

  const contentStyle = useAnimatedStyle(() => ({
    opacity: 1 - Math.min(iris.value * 2.6, 1),
    transform: [{ scale: 1 + iris.value * 0.45 }],
  }));

  const bloomStyle = useAnimatedStyle(() => ({ opacity: bloom.value * 0.5 }));

  const markStyle = useAnimatedStyle(() => ({
    opacity: markOpacity.value,
    // The bell rocks a little as it is struck.
    transform: [{ scale: markScale.value }, { rotate: `${striker.value * 0.07}deg` }],
  }));

  const wordStyle = useAnimatedStyle(() => ({
    opacity: wordOpacity.value,
    transform: [{ translateY: (1 - wordOpacity.value) * 14 }],
  }));

  const markProps = useAnimatedProps(() => ({ strikerRotation: striker.value }));

  return (
    <Pressable
      onPress={skip}
      accessibilityRole="button"
      accessibilityLabel="Skip the opening"
      style={[StyleSheet.absoluteFill, styles.host]}
    >
      <Animated.View
        style={[
          styles.iris,
          {
            width: irisRadius * 2,
            height: irisRadius * 2,
            borderRadius: irisRadius,
            top: height / 2 - irisRadius,
            left: width / 2 - irisRadius,
          },
          irisStyle,
        ]}
      >
        <Field size={irisRadius * 2} />
        <Animated.View style={[StyleSheet.absoluteFill, bloomStyle]}>
          <Bloom size={irisRadius * 2} />
        </Animated.View>
      </Animated.View>

      <Animated.View style={[styles.content, contentStyle]}>
        <View style={styles.stage}>
          {reduceMotion
            ? null
            : rings.map((ring, index) => (
                <Ring key={index} progress={ring} maximumRadius={ringLimit} />
              ))}
          <Animated.View style={markStyle}>
            <AnimatedDawuroMark
              colour={colour.cream}
              size={MARK_SIZE}
              animatedProps={markProps}
            />
          </Animated.View>
        </View>

        <Animated.View style={[styles.words, wordStyle]}>
          <Text style={styles.wordmark}>Dawuro</Text>
          <View style={styles.rule} />
          <Text style={styles.tagline}>HEALTH WEATHER FOR EVERY DISTRICT</Text>
        </Animated.View>
      </Animated.View>
    </Pressable>
  );
}

/**
 * The field is one deep hue lit from behind the bell, not a flat fill. A single colour
 * deepening outward is depth; two hues sliding into each other is decoration, and it is
 * the first thing that makes a screen look generated.
 */
function Field({ size }: { size: number }) {
  return (
    <Svg width={size} height={size} style={StyleSheet.absoluteFill}>
      <Defs>
        <RadialGradient id="field" cx="50%" cy="46%" r="62%">
          <Stop offset="0%" stopColor="#12463D" />
          <Stop offset="58%" stopColor="#0A322C" />
          <Stop offset="100%" stopColor="#05201C" />
        </RadialGradient>
      </Defs>
      <Rect width={size} height={size} fill="url(#field)" />
    </Svg>
  );
}

/** The flash of warmth on each strike, as if the iron rang light as well as sound. */
function Bloom({ size }: { size: number }) {
  return (
    <Svg width={size} height={size} style={StyleSheet.absoluteFill}>
      <Defs>
        <RadialGradient id="bloom" cx="50%" cy="46%" r="34%">
          <Stop offset="0%" stopColor={colour.ochre} stopOpacity={0.6} />
          <Stop offset="100%" stopColor={colour.ochre} stopOpacity={0} />
        </RadialGradient>
      </Defs>
      <Rect width={size} height={size} fill="url(#bloom)" />
    </Svg>
  );
}

/** One ring leaving the bell, thinning and fading as the sound loses energy. */
function Ring({
  progress,
  maximumRadius,
}: {
  progress: SharedValue<number>;
  maximumRadius: number;
}) {
  const animatedProps = useAnimatedProps(() => ({
    r: RING_START_RADIUS + progress.value * maximumRadius,
    opacity: progress.value === 0 ? 0 : (1 - progress.value) ** 1.9 * 0.62,
    strokeWidth: 2.6 - progress.value * 1.7,
  }));

  const size = (RING_START_RADIUS + maximumRadius) * 2 + 8;
  const inset = (MARK_SIZE - size) / 2;

  return (
    <Svg
      width={size}
      height={size}
      style={{ position: "absolute", left: inset, top: inset }}
      pointerEvents="none"
    >
      <AnimatedCircle
        cx={size / 2}
        cy={size / 2}
        animatedProps={animatedProps}
        stroke={colour.ochre}
        fill="none"
      />
    </Svg>
  );
}

const styles = StyleSheet.create({
  host: { alignItems: "center", justifyContent: "center", zIndex: 10 },
  iris: { position: "absolute", overflow: "hidden" },
  content: { alignItems: "center" },
  stage: {
    width: MARK_SIZE,
    height: MARK_SIZE,
    alignItems: "center",
    justifyContent: "center",
  },
  words: { alignItems: "center", marginTop: space.generous },
  wordmark: {
    ...type.verdict,
    fontFamily: family.display,
    color: colour.cream,
  },
  rule: {
    width: 34,
    height: 1.5,
    backgroundColor: colour.ochre,
    opacity: 0.7,
    marginTop: space.comfortable,
    marginBottom: space.comfortable,
  },
  tagline: {
    ...type.caption,
    fontFamily: family.bodyMedium,
    color: colour.cream,
    opacity: 0.6,
    letterSpacing: 1.1,
  },
});
