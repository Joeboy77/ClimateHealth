import { GlobeHemisphereWest, MapPinLine } from "@phosphor-icons/react";

import type { UserResponse } from "@/lib/api/types";

function districtLabel(districtId: string | null): string {
  if (!districtId) return "one district";
  return districtId
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function ScopeBadge({ user }: { user: UserResponse }) {
  const national = user.scope.level === "national";
  const Icon = national ? GlobeHemisphereWest : MapPinLine;
  const label = national
    ? "National access"
    : `Scoped to ${districtLabel(user.scope.district_id)}`;

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-raised)] px-2 py-1 text-xs text-[var(--color-muted)]"
      title={
        national
          ? "You can view every district"
          : "You can only view your own district"
      }
    >
      <Icon aria-hidden className="size-3.5" />
      <span>{label}</span>
    </span>
  );
}
