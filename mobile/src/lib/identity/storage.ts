import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

/**
 * Where the Guardian's token lives.
 *
 * On a device it goes into the keychain, because it is a bearer credential and the phone
 * may be shared or lost. The web preview has no keychain, so it holds the value in memory
 * for the session and forgets it: the preview is a development convenience and should not
 * be quietly persisting credentials in a browser.
 */

const memory = new Map<string, string>();
const onDevice = Platform.OS !== "web";

export async function readSecret(key: string): Promise<string | null> {
  if (!onDevice) return memory.get(key) ?? null;
  try {
    return await SecureStore.getItemAsync(key);
  } catch {
    return null;
  }
}

export async function writeSecret(key: string, value: string): Promise<void> {
  if (!onDevice) {
    memory.set(key, value);
    return;
  }
  await SecureStore.setItemAsync(key, value);
}

export async function clearSecret(key: string): Promise<void> {
  if (!onDevice) {
    memory.delete(key);
    return;
  }
  await SecureStore.deleteItemAsync(key);
}
