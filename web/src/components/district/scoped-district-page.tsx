"use client";

import { useState, type ReactNode } from "react";

import { DistrictSwitcher } from "@/components/district/district-switcher";
import { RequireSession } from "@/components/shell/require-session";
import { useAuthenticatedSession } from "@/lib/auth/session";

/**
 * Shared frame for district-scoped screens. A district officer lands straight in
 * their own district with no chooser; a national officer picks one.
 */
export function ScopedDistrictPage({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: (context: { token: string; districtId: string }) => ReactNode;
}) {
  return (
    <RequireSession>
      <ScopedDistrictBody title={title} description={description}>
        {children}
      </ScopedDistrictBody>
    </RequireSession>
  );
}

function ScopedDistrictBody({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: (context: { token: string; districtId: string }) => ReactNode;
}) {
  const { token, user } = useAuthenticatedSession();
  const scopedDistrictId =
    user?.scope.level === "district" ? user.scope.district_id : null;
  const [chosen, setChosen] = useState<string | null>(null);

  const districtId = scopedDistrictId ?? chosen;

  return (
    <div className="mx-auto max-w-[1400px] px-6 py-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-h1">{title}</h1>
          <p className="mt-1 text-small text-[var(--color-muted)]">
            {description}
          </p>
        </div>
        {scopedDistrictId === null ? (
          <DistrictSwitcher
            token={token}
            value={districtId}
            onChange={setChosen}
            className="w-64"
          />
        ) : null}
      </header>

      <div className="mt-5">
        {districtId === null ? (
          <p className="text-small text-[var(--color-muted)]">
            Choose a district to continue.
          </p>
        ) : (
          children({ token, districtId })
        )}
      </div>
    </div>
  );
}
