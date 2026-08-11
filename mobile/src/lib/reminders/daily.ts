import * as Notifications from "expo-notifications";
import { Platform } from "react-native";

import { persistent } from "@/lib/offline/store";

const ENABLED_KEY = "dawuro.reminder.enabled";
const IDENTIFIER = "dawuro-daily-run";

/**
 * The morning reminder.
 *
 * Seven in the morning, once a day, in the person's own timezone: early enough to act
 * before the day starts, and never a second time. A health application that pings people
 * repeatedly to protect a streak is using anxiety as a growth tactic, and the people this
 * is built for have enough of that already.
 *
 * It is off until somebody turns it on, and one tap turns it off again for good.
 */

const REMINDER_HOUR = 7;

const LINES = [
  "Today's warning is ready. One minute to read it.",
  "Your district has a forecast waiting.",
  "A short run today keeps your streak going.",
] as const;

export function reminderEnabled(): boolean {
  return persistent().getString(ENABLED_KEY) === "true";
}

export async function enableReminder(): Promise<boolean> {
  const existing = await Notifications.getPermissionsAsync();
  const granted =
    existing.granted || (await Notifications.requestPermissionsAsync()).granted;

  if (!granted) return false;

  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("daily", {
      name: "Daily warning",
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }

  await Notifications.cancelScheduledNotificationAsync(IDENTIFIER).catch(
    () => undefined,
  );
  await Notifications.scheduleNotificationAsync({
    identifier: IDENTIFIER,
    content: {
      title: "Dawuro",
      body: LINES[new Date().getDate() % LINES.length] ?? LINES[0],
    },
    trigger: {
      type: Notifications.SchedulableTriggerInputTypes.DAILY,
      hour: REMINDER_HOUR,
      minute: 0,
    },
  });

  persistent().set(ENABLED_KEY, "true");
  return true;
}

export async function disableReminder(): Promise<void> {
  await Notifications.cancelScheduledNotificationAsync(IDENTIFIER).catch(
    () => undefined,
  );
  persistent().set(ENABLED_KEY, "false");
}
