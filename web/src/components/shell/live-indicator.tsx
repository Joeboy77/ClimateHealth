"use client";

import { useEffect, useState } from "react";

import type { ConnectionState, LiveEvent } from "@/lib/live/use-live-events";
import { cn } from "@/lib/cn";

const FLASH_DURATION_MS = 4_000;

const STATE_COPY: Record<ConnectionState, string> = {
  connecting: "Connecting",
  live: "Live",
  offline: "Reconnecting",
};

const STATE_DOT: Record<ConnectionState, string> = {
  connecting: "bg-[var(--color-muted)]",
  live: "bg-[var(--color-risk-low)]",
  offline: "bg-[var(--color-risk-moderate)]",
};

export function LiveIndicator({
  state,
  lastEvent,
}: {
  state: ConnectionState;
  lastEvent: LiveEvent | null;
}) {
  const [flash, setFlash] = useState<LiveEvent | null>(null);

  useEffect(() => {
    if (!lastEvent) return;
    setFlash(lastEvent);
    const timer = setTimeout(() => setFlash(null), FLASH_DURATION_MS);
    return () => clearTimeout(timer);
  }, [lastEvent]);

  return (
    <span
      className={cn(
        "flex items-center gap-2 rounded-[var(--radius-sm)] border px-2 py-1",
        "transition-colors duration-[var(--duration-medium)]",
        flash
          ? "border-[var(--color-accent)]/40 bg-[var(--color-accent-subtle)]"
          : "border-[var(--color-border)] bg-[var(--color-raised)]",
      )}
      aria-live="polite"
    >
      <span className="relative flex size-2">
        {state === "live" ? (
          <span
            aria-hidden
            className="absolute inline-flex size-full animate-ping rounded-full bg-[var(--color-risk-low)] opacity-60"
          />
        ) : null}
        <span
          aria-hidden
          className={cn(
            "relative inline-flex size-2 rounded-full",
            STATE_DOT[state],
          )}
        />
      </span>
      <span
        className={cn(
          "max-w-[22rem] truncate text-xs",
          flash ? "text-[var(--color-accent)]" : "text-[var(--color-muted)]",
        )}
      >
        {flash ? flash.summary : STATE_COPY[state]}
      </span>
    </span>
  );
}
