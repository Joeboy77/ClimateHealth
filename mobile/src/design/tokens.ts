/**
 * The single source of style for Dawuro.
 *
 * The agency console is a cool, dense operations instrument. This is warm, plain and
 * read at arm's length in Ghanaian sunlight. The one thing both must share is the risk
 * scale: red means the same fact to a citizen and to a health officer.
 */

export const colour = {
  /** Warm clay, not grey and not pure white. Holds up under bright light. */
  canvas: "#F7F2EA",
  surface: "#FFFFFF",
  raised: "#F1EADF",
  border: "#E2D8C9",
  borderStrong: "#CBBDA8",

  ink: "#1C1A17",
  inkMuted: "#6B655C",
  inkFaint: "#9A9287",

  /** Deep forest, the platform's signature. Carried over from the console. */
  accent: "#0E6E63",
  accentPressed: "#0B564D",
  accentSubtle: "#DDEDE9",
  onAccent: "#FFFFFF",

  /** Shared with the console, unchanged. Colour is never the only carrier. */
  riskLow: "#1F7A5C",
  riskLowSurface: "#E4F1EA",
  riskModerate: "#B07908",
  riskModerateSurface: "#FBF0D9",
  riskHigh: "#C4551F",
  riskHighSurface: "#FBE8DC",
  riskSevere: "#A32118",
  riskSevereSurface: "#FAE4E1",

  /** Simulated or demo data is always visually declared, never passed off as real. */
  simulated: "#5B54A8",
  simulatedSurface: "#EAE8F6",

  /**
   * The opening moment. A deep forest field the clay canvas rises out of, with a warm
   * ochre for the struck-bell rings. Green and ochre on warm cream is a Ghanaian palette
   * arrived at through material rather than through flags and kente prints, which is what
   * "make it African" produces when nobody is thinking.
   */
  field: "#0A3B35",
  fieldDeep: "#062621",
  cream: "#F6EFE3",
  ochre: "#D39A2E",
  ochreDeep: "#A8741B",
} as const;

/**
 * Two families, chosen to sound like a person rather than a system.
 *
 * Fraunces carries the verdict: a warm, slightly old-style serif with the authority of a
 * public notice. Inter carries everything else, because a warning has to stay legible at
 * small sizes on a cheap screen and a serif does not.
 */
export const family = {
  display: "Fraunces_600SemiBold",
  body: "Inter_400Regular",
  bodyMedium: "Inter_500Medium",
  bodySemibold: "Inter_600SemiBold",
} as const;

/**
 * A type scale with only the sizes we actually use. Every size is paired with a line
 * height, because unpaired sizes are how mobile type ends up cramped.
 */
export const type = {
  verdict: { fontSize: 44, lineHeight: 48, letterSpacing: -1 },
  display: { fontSize: 29, lineHeight: 36, letterSpacing: -0.4 },
  title: { fontSize: 21, lineHeight: 27, letterSpacing: -0.2 },
  heading: { fontSize: 17, lineHeight: 23, letterSpacing: -0.1 },
  body: { fontSize: 16, lineHeight: 24, letterSpacing: 0 },
  small: { fontSize: 14, lineHeight: 20, letterSpacing: 0 },
  caption: { fontSize: 12.5, lineHeight: 17, letterSpacing: 0.1 },
  overline: { fontSize: 11.5, lineHeight: 15, letterSpacing: 0.7 },
} as const;

export const weight = {
  regular: "400",
  medium: "500",
  semibold: "600",
} as const;

/** A 4pt rhythm. Named for intent so spacing decisions stay consistent. */
export const space = {
  hair: 2,
  tight: 4,
  snug: 8,
  base: 12,
  comfortable: 16,
  roomy: 24,
  generous: 32,
  section: 48,
} as const;

export const radius = {
  sm: 8,
  md: 12,
  lg: 18,
  xl: 26,
  pill: 999,
} as const;

/**
 * Elevation is used sparingly and always warm-tinted: a neutral black shadow on a clay
 * canvas reads as dirt.
 */
export const elevation = {
  resting: {
    shadowColor: "#4A3B26",
    shadowOpacity: 0.07,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 3 },
    elevation: 2,
  },
  lifted: {
    shadowColor: "#4A3B26",
    shadowOpacity: 0.12,
    shadowRadius: 22,
    shadowOffset: { width: 0, height: 10 },
    elevation: 8,
  },
} as const;

/** The smallest touch target we ship. Proposal section 13.4. */
export const MINIMUM_TARGET = 48;
