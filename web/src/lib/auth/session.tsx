"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api, ApiError } from "@/lib/api/client";
import type { UserResponse } from "@/lib/api/types";

const TOKEN_STORAGE_KEY = "climahealth.token";

type SessionState = {
  token: string | null;
  user: UserResponse | null;
  status: "loading" | "authenticated" | "anonymous";
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => void;
};

const SessionContext = createContext<SessionState | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserResponse | null>(null);
  const [status, setStatus] = useState<SessionState["status"]>("loading");

  useEffect(() => {
    const stored = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!stored) {
      setStatus("anonymous");
      return;
    }

    api
      .me(stored)
      .then((identity) => {
        setToken(stored);
        setUser(identity);
        setStatus("authenticated");
      })
      .catch((error: unknown) => {
        if (error instanceof ApiError && error.isUnauthorised) {
          window.localStorage.removeItem(TOKEN_STORAGE_KEY);
        }
        setStatus("anonymous");
      });
  }, []);

  const signIn = useCallback(async (username: string, password: string) => {
    const session = await api.login(username, password);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, session.access_token);
    setToken(session.access_token);
    setUser(session.user);
    setStatus("authenticated");
  }, []);

  const signOut = useCallback(() => {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
    setStatus("anonymous");
  }, []);

  const value = useMemo<SessionState>(
    () => ({ token, user, status, signIn, signOut }),
    [token, user, status, signIn, signOut],
  );

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

export function useSession(): SessionState {
  const context = useContext(SessionContext);
  if (context === null) {
    throw new Error("useSession must be used inside a SessionProvider");
  }
  return context;
}

export function useAuthenticatedSession(): SessionState & { token: string } {
  const session = useSession();
  if (session.token === null) {
    throw new Error("This view requires an authenticated session");
  }
  return { ...session, token: session.token };
}
