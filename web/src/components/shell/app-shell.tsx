"use client";

import { Building2, LogOut } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import { LiveIndicator } from "@/components/shell/live-indicator";
import { NavRail } from "@/components/shell/nav-rail";
import { ScopeBadge } from "@/components/shell/scope-badge";
import { ThemeToggle } from "@/components/shell/theme-toggle";
import { Button } from "@/components/ui/button";
import { useSession } from "@/lib/auth/session";
import { useLiveEvents } from "@/lib/live/use-live-events";

const RAIL_STORAGE_KEY = "climahealth.rail";

export function AppShell({ children }: { children: ReactNode }) {
  const { user, token, signOut } = useSession();
  const { state, lastEvent } = useLiveEvents(token);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    setCollapsed(window.localStorage.getItem(RAIL_STORAGE_KEY) === "collapsed");
  }, []);

  const toggleRail = () =>
    setCollapsed((previous) => {
      const next = !previous;
      window.localStorage.setItem(
        RAIL_STORAGE_KEY,
        next ? "collapsed" : "expanded",
      );
      return next;
    });

  return (
    <div className="flex h-dvh overflow-hidden">
      <NavRail collapsed={collapsed} onToggle={toggleRail} />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-end gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-5">
          <LiveIndicator state={state} lastEvent={lastEvent} />
          {user ? (
            <span className="hidden items-center gap-1.5 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-raised)] px-2 py-1 text-xs text-[var(--color-muted)] sm:flex">
              <Building2 aria-hidden strokeWidth={2} className="size-3.5" />
              {user.agency.name}
            </span>
          ) : null}
          {user ? <ScopeBadge user={user} /> : null}
          <ThemeToggle />
          {user ? (
            <Button variant="ghost" size="sm" onClick={signOut}>
              <LogOut aria-hidden strokeWidth={2} className="size-4" />
              Sign out
            </Button>
          ) : null}
        </header>
        <main className="min-w-0 flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
