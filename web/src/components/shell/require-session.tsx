"use client";

import { LoaderCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { AppShell } from "@/components/shell/app-shell";
import { useSession } from "@/lib/auth/session";

export function RequireSession({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { status } = useSession();

  useEffect(() => {
    if (status === "anonymous") router.replace("/sign-in");
  }, [status, router]);

  if (status !== "authenticated") {
    return (
      <div className="grid min-h-dvh place-items-center">
        <LoaderCircle
          aria-label="Checking your session"
          className="size-5 animate-spin text-[var(--color-muted)]"
        />
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}
