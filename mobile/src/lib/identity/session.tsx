import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { clearSecret, readSecret, writeSecret } from "./storage";
import type { CitizenIdentity, CitizenSession } from "@/lib/api/types";

const TOKEN_KEY = "dawuro.token";
const CITIZEN_KEY = "dawuro.citizen";

type Session = {
  /** Null while the stored session is still being read. */
  readonly loading: boolean;
  readonly token: string | null;
  readonly citizen: CitizenIdentity | null;
  readonly join: (session: CitizenSession) => Promise<void>;
  readonly leave: () => Promise<void>;
};

const SessionContext = createContext<Session | null>(null);

/**
 * The signed-in Guardian.
 *
 * A registration is kept on the phone so somebody joins once and then simply opens the
 * app each morning. That is the whole product: a daily habit. Asking a person to sign in
 * to read a weather warning would be absurd.
 */
export function SessionProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [citizen, setCitizen] = useState<CitizenIdentity | null>(null);

  useEffect(() => {
    let cancelled = false;

    const restore = async () => {
      const [storedToken, storedCitizen] = await Promise.all([
        readSecret(TOKEN_KEY),
        readSecret(CITIZEN_KEY),
      ]);
      if (cancelled) return;

      setToken(storedToken);
      if (storedCitizen !== null) {
        try {
          setCitizen(JSON.parse(storedCitizen) as CitizenIdentity);
        } catch {
          // A record we cannot parse is a record we should not trust.
          setCitizen(null);
        }
      }
      setLoading(false);
    };

    void restore();
    return () => {
      cancelled = true;
    };
  }, []);

  const join = useCallback(async (session: CitizenSession) => {
    await Promise.all([
      writeSecret(TOKEN_KEY, session.access_token),
      writeSecret(CITIZEN_KEY, JSON.stringify(session.citizen)),
    ]);
    setToken(session.access_token);
    setCitizen(session.citizen);
  }, []);

  const leave = useCallback(async () => {
    await Promise.all([clearSecret(TOKEN_KEY), clearSecret(CITIZEN_KEY)]);
    setToken(null);
    setCitizen(null);
  }, []);

  const value = useMemo<Session>(
    () => ({ loading, token, citizen, join, leave }),
    [loading, token, citizen, join, leave],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): Session {
  const session = useContext(SessionContext);
  if (session === null) {
    throw new Error("useSession must be used inside a SessionProvider");
  }
  return session;
}

/** For screens that only render once a Guardian exists. */
export function useGuardian(): { token: string; citizen: CitizenIdentity } {
  const { token, citizen } = useSession();
  if (token === null || citizen === null) {
    throw new Error("This screen requires a registered Guardian");
  }
  return { token, citizen };
}
