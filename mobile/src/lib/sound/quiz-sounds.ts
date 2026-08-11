import { createAudioPlayer, setAudioModeAsync, type AudioPlayer } from "expo-audio";

import { persistent } from "@/lib/offline/store";

/**
 * The three quiz sounds.
 *
 * A right answer rings, a wrong one lands softly, and a finished run climbs. The
 * wrong tone is deliberately gentle and low rather than a buzzer: the reader is
 * somebody learning how to keep their household well, and a harsh noise in a
 * public place is a good reason to stop playing.
 *
 * Players are created once and rewound rather than rebuilt, so a fast tapper does
 * not stack up native players. Everything here fails quietly; a device that will
 * not play audio should still let somebody finish a quiz.
 */

const MUTED_KEY = "dawuro.sound.muted";

const SOURCES = {
  correct: require("../../../assets/sounds/correct.wav"),
  wrong: require("../../../assets/sounds/wrong.wav"),
  finished: require("../../../assets/sounds/finished.wav"),
} as const;

export type QuizSound = keyof typeof SOURCES;

let players: Record<QuizSound, AudioPlayer> | null = null;
let modeConfigured = false;

export function soundMuted(): boolean {
  return persistent().getString(MUTED_KEY) === "true";
}

export function setSoundMuted(muted: boolean): void {
  persistent().set(MUTED_KEY, muted ? "true" : "false");
}

function configureMode(): void {
  if (modeConfigured) return;
  modeConfigured = true;
  // A quiz sound must not silence somebody's music or duck a call, and on iOS it
  // should still be heard when the ringer switch is off.
  void setAudioModeAsync({
    playsInSilentMode: true,
    shouldPlayInBackground: false,
    interruptionMode: "mixWithOthers",
  }).catch(() => undefined);
}

export function prepareQuizSounds(): void {
  if (players !== null) return;
  configureMode();
  try {
    players = {
      correct: createAudioPlayer(SOURCES.correct),
      wrong: createAudioPlayer(SOURCES.wrong),
      finished: createAudioPlayer(SOURCES.finished),
    };
  } catch {
    players = null;
  }
}

export function playQuizSound(sound: QuizSound): void {
  if (soundMuted()) return;
  prepareQuizSounds();

  const player = players?.[sound];
  if (player === undefined) return;

  try {
    void player.seekTo(0).catch(() => undefined);
    player.play();
  } catch {
    // A device that will not play audio is not a reason to interrupt the run.
  }
}

export function releaseQuizSounds(): void {
  if (players === null) return;
  for (const player of Object.values(players)) {
    try {
      player.remove();
    } catch {
      // Already gone.
    }
  }
  players = null;
}
