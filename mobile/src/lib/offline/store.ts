import { Platform } from "react-native";
import Constants from "expo-constants";

/**
 * Small persistent key-value storage, for data rather than credentials.
 *
 * MMKV on a device, because the report queue and the last forecast are read on every
 * launch and a synchronous read keeps that off the critical path. It is a Nitro native
 * module, so it is loaded lazily and never touched on web.
 *
 * On web it uses localStorage. That is deliberately different from where the session
 * token lives: a queued report and yesterday's forecast are the user's own data and
 * public information respectively, whereas a bearer token in browser storage is a
 * credential sitting somewhere it need not be. Keeping them apart also means the offline
 * behaviour can actually be exercised in the preview rather than only on a phone.
 */

type KeyValueStore = {
  readonly getString: (key: string) => string | undefined;
  readonly set: (key: string, value: string) => void;
  readonly delete: (key: string) => void;
};

function memoryStore(): KeyValueStore {
  const values = new Map<string, string>();
  return {
    getString: (key) => values.get(key),
    set: (key, value) => {
      values.set(key, value);
    },
    delete: (key) => {
      values.delete(key);
    },
  };
}

function browserStore(): KeyValueStore {
  return {
    getString: (key) => window.localStorage.getItem(key) ?? undefined,
    set: (key, value) => window.localStorage.setItem(key, value),
    delete: (key) => window.localStorage.removeItem(key),
  };
}

function nativeStore(): KeyValueStore {
  const isExpoGo =
    Constants.appOwnership === "expo" || Constants.executionEnvironment === "storeClient";
  if (Platform.OS === "web" || isExpoGo) return memoryStore();

  // Required inline so the web bundle never reaches for a native module.
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { createMMKV } =
    require("react-native-mmkv") as typeof import("react-native-mmkv");
  const storage = createMMKV({ id: "dawuro" });
  return {
    getString: (key) => storage.getString(key),
    set: (key, value) => storage.set(key, value),
    delete: (key) => {
      storage.remove(key);
    },
  };
}

let store: KeyValueStore | null = null;

export function persistent(): KeyValueStore {
  if (store !== null) return store;
  try {
    store = Platform.OS === "web" ? browserStore() : nativeStore();
  } catch {
    // A phone that cannot open its own storage should still run, just without a
    // durable queue. Losing a queued report is bad; refusing to start is worse.
    store = memoryStore();
  }
  return store;
}
