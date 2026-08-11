"use client";

import { useQuery } from "@tanstack/react-query";
import { CaretDown } from "@phosphor-icons/react";

import { api } from "@/lib/api/client";
import { cn } from "@/lib/cn";

/**
 * National users choose which district to work on. District users never see this:
 * their scope already fixes the answer, so the surrounding page renders directly.
 */
export function DistrictSwitcher({
  token,
  value,
  onChange,
  className,
}: {
  token: string;
  value: string | null;
  onChange: (districtId: string) => void;
  className?: string;
}) {
  const districts = useQuery({
    queryKey: ["districts"],
    queryFn: () => api.districts(token),
  });

  return (
    <div className={cn("relative", className)}>
      <label htmlFor="district-switcher" className="sr-only">
        Choose a district
      </label>
      <select
        id="district-switcher"
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        disabled={districts.isPending}
        className="h-9 w-full appearance-none rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] pl-3 pr-9 text-small text-[var(--color-ink)] transition-colors duration-[var(--duration-instant)] hover:border-[var(--color-border-strong)]"
      >
        {value === null ? <option value="">Choose a district</option> : null}
        {(districts.data ?? []).map((district) => (
          <option key={district.district_id} value={district.district_id}>
            {district.name} — {district.region}
          </option>
        ))}
      </select>
      <CaretDown
        aria-hidden
        className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-[var(--color-muted)]"
      />
    </div>
  );
}
