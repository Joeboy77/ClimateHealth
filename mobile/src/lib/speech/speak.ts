import * as Speech from "expo-speech";

import type { NarrationLanguage } from "@/lib/api/types";

/**
 * Reading the warning aloud.
 *
 * Proposal section 13: every essential function travels through text, audio and visual at
 * once, so a limitation in one channel is always covered by another. A Voice-First
 * Guardian who cannot read the screen is exactly who this is for.
 *
 * The rule that shapes the whole module: **never speak text in a voice that does not
 * match its language.** An English voice reading Twi produces noise, and noise delivered
 * confidently is worse than silence, because the person cannot tell it is wrong. If the
 * phone has no voice for the language the content is in, the control says so and stays
 * quiet.
 */

/** What each language would need from the operating system's voice list. */
const VOICE_PREFIXES: Record<string, readonly string[]> = {
  en: ["en"],
  // Akan/Twi. Almost no phone ships this today, which is the point of checking rather
  // than assuming.
  tw: ["ak", "tw"],
  gaa: ["gaa", "ga"],
  ee: ["ee"],
  dag: ["dag"],
};

/** Slower than default: this is a health instruction, not a podcast. */
const SPEAKING_RATE = 0.92;

export type Speakable = {
  readonly text: string;
  readonly language: NarrationLanguage;
};

let cachedVoices: Speech.Voice[] | null = null;

async function voices(): Promise<Speech.Voice[]> {
  if (cachedVoices !== null) return cachedVoices;
  try {
    cachedVoices = await Speech.getAvailableVoicesAsync();
  } catch {
    cachedVoices = [];
  }
  return cachedVoices;
}

export async function voiceFor(
  language: NarrationLanguage,
): Promise<Speech.Voice | null> {
  const prefixes = VOICE_PREFIXES[language] ?? [];
  const available = await voices();

  for (const prefix of prefixes) {
    const match = available.find((voice) =>
      voice.language.toLowerCase().startsWith(prefix),
    );
    if (match !== undefined) return match;
  }
  return null;
}

export async function canSpeak(language: NarrationLanguage): Promise<boolean> {
  // An empty voice list means the platform did not tell us, not that it cannot speak.
  // Web reports voices asynchronously and often late, so English is assumed available.
  const available = await voices();
  if (available.length === 0) return language === "en";
  return (await voiceFor(language)) !== null;
}

export async function speak(
  parts: readonly Speakable[],
  onDone: () => void,
): Promise<void> {
  await stop();

  const spoken = parts.filter((part) => part.text.trim().length > 0);
  if (spoken.length === 0) {
    onDone();
    return;
  }

  spoken.forEach((part, index) => {
    const last = index === spoken.length - 1;
    void Speech.speak(part.text, {
      language: part.language,
      rate: SPEAKING_RATE,
      onDone: last ? onDone : undefined,
      onStopped: last ? onDone : undefined,
      onError: last ? onDone : undefined,
    });
  });
}

export async function stop(): Promise<void> {
  try {
    await Speech.stop();
  } catch {
    // Nothing was speaking. Stopping silence is not an error worth surfacing.
  }
}
