"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Broadcast, CircleNotch, CloudRain, Sun } from "@phosphor-icons/react";

import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { api } from "@/lib/api/client";
import type { FeatureProvenance } from "@/lib/api/types";
import { cn } from "@/lib/cn";

const SCENARIOS = [
  {
    id: "heavy_rain",
    label: "Heavy rain",
    icon: CloudRain,
    description: "120 mm over 7 days, 85% humidity, wet season",
  },
  {
    id: "dry_and_dusty",
    label: "Dry and dusty",
    icon: Sun,
    description: "40 dry days, 18% humidity, 120 µg/m³ dust, dry season",
  },
] as const;

export function DataSourceControl({
  token,
  districtId,
  provenance,
  observedOn,
}: {
  token: string;
  districtId: string;
  provenance: FeatureProvenance;
  observedOn: string;
}) {
  const queryClient = useQueryClient();
  const isLive = provenance === "live";

  const refresh = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: ["district", districtId] }),
      queryClient.invalidateQueries({ queryKey: ["forecast", districtId] }),
      queryClient.invalidateQueries({ queryKey: ["districts"] }),
      queryClient.invalidateQueries({ queryKey: ["alerts"] }),
    ]);

  const useLive = useMutation({
    mutationFn: () => api.clearDemoConditions(token, districtId),
    onSuccess: refresh,
  });

  const useScenario = useMutation({
    mutationFn: (scenario: string) =>
      api.setDemoConditions(token, districtId, scenario),
    onSuccess: refresh,
  });

  const busy = useLive.isPending || useScenario.isPending;

  return (
    <Card>
      <CardHeader
        title="Climate data source"
        description="Switch between live observations and a reproducible scenario."
      />
      <CardBody className="space-y-3">
        <div
          className={cn(
            "flex items-start gap-2.5 rounded-[var(--radius-md)] border px-3 py-2.5",
            isLive
              ? "border-[var(--color-accent)]/30 bg-[var(--color-accent-subtle)]"
              : "border-[var(--color-confidence-demo)]/30 bg-[var(--color-confidence-demo-surface)]",
          )}
        >
          <Broadcast
            aria-hidden
            className={cn(
              "mt-0.5 size-4 shrink-0",
              isLive
                ? "text-[var(--color-accent)]"
                : "text-[var(--color-confidence-demo)]",
            )}
          />
          <div className="min-w-0">
            <p
              className={cn(
                "text-small font-medium",
                isLive
                  ? "text-[var(--color-accent)]"
                  : "text-[var(--color-confidence-demo)]",
              )}
            >
              {isLive ? "Live Open-Meteo observations" : "Simulated conditions"}
            </p>
            <p className="mt-0.5 text-[0.75rem] text-[var(--color-muted)]">
              {isLive
                ? `Measured at this district's coordinates, last observation ${observedOn}.`
                : "Overridden for demonstration. The engine still decides risk from these readings."}
            </p>
          </div>
        </div>

        <div className="grid gap-2">
          <button
            type="button"
            onClick={() => useLive.mutate()}
            disabled={busy || isLive}
            className={cn(
              "flex items-center gap-2.5 rounded-[var(--radius-md)] border px-3 py-2 text-left",
              "transition-colors duration-[var(--duration-instant)]",
              "disabled:cursor-default disabled:opacity-55",
              isLive
                ? "border-[var(--color-accent)]/40 bg-[var(--color-accent-subtle)]"
                : "border-[var(--color-border)] hover:border-[var(--color-border-strong)] hover:bg-[var(--color-raised)]",
            )}
          >
            {useLive.isPending ? (
              <CircleNotch
                aria-hidden
                className="size-4 shrink-0 animate-spin"
              />
            ) : (
              <Broadcast aria-hidden className="size-4 shrink-0" />
            )}
            <span className="min-w-0">
              <span className="block text-small font-medium">
                Live climate data
              </span>
              <span className="block text-[0.75rem] text-[var(--color-muted)]">
                Fetch this district&rsquo;s current readings from Open-Meteo
              </span>
            </span>
          </button>

          {SCENARIOS.map(({ id, label, icon: Icon, description }) => (
            <button
              key={id}
              type="button"
              onClick={() => useScenario.mutate(id)}
              disabled={busy}
              className={cn(
                "flex items-center gap-2.5 rounded-[var(--radius-md)] border border-[var(--color-border)] px-3 py-2 text-left",
                "transition-colors duration-[var(--duration-instant)]",
                "hover:border-[var(--color-border-strong)] hover:bg-[var(--color-raised)]",
                "disabled:cursor-default disabled:opacity-55",
              )}
            >
              {useScenario.isPending && useScenario.variables === id ? (
                <CircleNotch
                  aria-hidden
                  className="size-4 shrink-0 animate-spin"
                />
              ) : (
                <Icon aria-hidden className="size-4 shrink-0" />
              )}
              <span className="min-w-0">
                <span className="block text-small font-medium">{label}</span>
                <span className="block text-[0.75rem] text-[var(--color-muted)]">
                  {description}
                </span>
              </span>
            </button>
          ))}
        </div>

        {useLive.isError || useScenario.isError ? (
          <p
            role="alert"
            className="text-[0.75rem] text-[var(--color-risk-severe)]"
          >
            {(useLive.error ?? useScenario.error)?.message}
          </p>
        ) : null}
      </CardBody>
    </Card>
  );
}
