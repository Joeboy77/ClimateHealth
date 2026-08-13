"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createSyncStoragePersister } from "@tanstack/query-sync-storage-persister";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import { ThemeProvider } from "next-themes";
import { useState, type ReactNode } from "react";

import { ApiError } from "@/lib/api/client";
import { SessionProvider } from "@/lib/auth/session";

const STALE_TIME_MS = 60_000;
/** A day. The dashboard should open on yesterday's picture rather than on nothing,
 *  and a fresh answer replaces it a moment later. */
const KEPT_FOR_MS = 24 * 60 * 60 * 1000;
const CACHE_KEY = "climahealth.query-cache";

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: STALE_TIME_MS,
        gcTime: KEPT_FOR_MS,
        refetchOnWindowFocus: false,
        retry: (failureCount, error) => {
          if (error instanceof ApiError && error.status < 500) return false;
          return failureCount < 2;
        },
      },
    },
  });
}

/**
 * The last picture, restored instantly.
 *
 * The national risk picture is 260 districts of computed output, and waiting on it
 * leaves an officer looking at empty boxes every time they open the platform. What
 * they saw last time is written to storage and painted immediately on the next visit,
 * then replaced the moment fresh data lands.
 *
 * Only queries are kept, never the session: a token in local storage outlives the tab
 * it was issued to, and that is not a trade worth making for a faster first paint.
 */
function createPersister() {
  if (typeof window === "undefined") return undefined;
  return createSyncStoragePersister({
    storage: window.localStorage,
    key: CACHE_KEY,
    throttleTime: 1_000,
  });
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createQueryClient);
  const [persister] = useState(createPersister);

  if (persister === undefined) {
    return (
      <ThemeProvider
        attribute="class"
        defaultTheme="dark"
        enableSystem={false}
        disableTransitionOnChange
      >
        <QueryClientProvider client={queryClient}>
          <SessionProvider>{children}</SessionProvider>
        </QueryClientProvider>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem={false}
      disableTransitionOnChange
    >
      <PersistQueryClientProvider
        client={queryClient}
        persistOptions={{ persister, maxAge: KEPT_FOR_MS, buster: "v1" }}
      >
        <SessionProvider>{children}</SessionProvider>
      </PersistQueryClientProvider>
    </ThemeProvider>
  );
}
