"use client";

import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  ChevronDown,
  Clock3,
  CloudRain,
  Factory,
  Sun,
  Users,
  Wind,
  Sprout,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import type { MatrixPathway } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { lagWindowText } from "@/lib/risk";

export default function MatrixPage() {
  const matrix = useQuery({
    queryKey: ["matrix"],
    queryFn: () => api.matrix(),
  });

  return (
    <div className="mx-auto max-w-[1100px] px-6 py-10">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-small text-[var(--color-muted)] transition-colors duration-[var(--duration-instant)] hover:text-[var(--color-ink)]"
      >
        <ArrowLeft aria-hidden strokeWidth={2} className="size-3.5" />
        Back to the platform
      </Link>

      <header className="mt-4">
        <p className="text-micro text-[var(--color-muted)]">
          Climate-Health Intelligence Matrix
        </p>
        <h1 className="mt-2 max-w-3xl text-display">
          Every climate signal, and the health consequences it implies
        </h1>
        <p className="mt-3 max-w-2xl text-small text-[var(--color-muted)]">
          This is the knowledge base the Signal-to-Syndrome Engine reasons over.
          Each pathway carries its own preconditions, weighted triggers, delay
          before cases appear, the group most affected, and the agencies that
          answer for it. Adding a condition means adding a pathway here, not
          rewriting the engine.
        </p>

        {matrix.data ? (
          <dl className="mt-6 flex flex-wrap gap-x-10 gap-y-3">
            <Figure label="Conditions" value={matrix.data.condition_count} />
            <Figure label="Climate drivers" value={matrix.data.driver_count} />
            <Figure label="Signals ingested" value={matrix.data.signal_count} />
          </dl>
        ) : null}
      </header>

      {matrix.isPending ? (
        <div className="mt-8 space-y-4">
          {Array.from({ length: 3 }, (_, index) => (
            <Skeleton key={index} className="h-40 w-full" />
          ))}
        </div>
      ) : matrix.isError ? (
        <p className="mt-8 text-small text-[var(--color-muted)]">
          {matrix.error.message}
        </p>
      ) : (
        <div className="mt-8 space-y-6">
          {matrix.data.drivers.map((group) => (
            <Card key={group.driver}>
              <CardHeader
                title={group.driver_name}
                description={`${group.pathways.length} ${
                  group.pathways.length === 1 ? "pathway" : "pathways"
                }`}
                action={<DriverIcon driver={group.driver} />}
              />
              {group.pathways.length === 0 ? (
                <CardBody>
                  <p className="text-small text-[var(--color-muted)]">
                    No pathway implemented for this driver yet.
                  </p>
                </CardBody>
              ) : (
                <ul>
                  {group.pathways.map((pathway) => (
                    <PathwayRow key={pathway.condition} pathway={pathway} />
                  ))}
                </ul>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function Figure({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dd className="text-metric">{value}</dd>
      <dt className="mt-0.5 text-micro text-[var(--color-muted)]">{label}</dt>
    </div>
  );
}

function PathwayRow({ pathway }: { pathway: MatrixPathway }) {
  const [open, setOpen] = useState(false);

  return (
    <li className="border-b border-[var(--color-border)] last:border-b-0">
      <button
        type="button"
        onClick={() => setOpen((previous) => !previous)}
        aria-expanded={open}
        className="flex w-full items-center gap-4 px-5 py-3.5 text-left transition-colors duration-[var(--duration-instant)] hover:bg-[var(--color-raised)]"
      >
        <span className="w-7 shrink-0 rounded-[var(--radius-sm)] border border-[var(--color-border)] px-1 py-0.5 text-center text-[0.625rem] font-semibold text-[var(--color-muted)]">
          T{pathway.tier}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-h3">{pathway.condition_label}</span>
          <span className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[0.75rem] text-[var(--color-muted)]">
            <span className="flex items-center gap-1">
              <Clock3 aria-hidden strokeWidth={2} className="size-3" />
              {lagWindowText(pathway.lag_window)}
            </span>
            <span className="flex items-center gap-1">
              <Users aria-hidden strokeWidth={2} className="size-3" />
              {pathway.vulnerable_group}
            </span>
          </span>
        </span>
        <span className="hidden shrink-0 text-[0.6875rem] text-[var(--color-muted)] sm:block">
          {pathway.triggers.length} triggers
        </span>
        <ChevronDown
          aria-hidden
          strokeWidth={2}
          className={cn(
            "size-4 shrink-0 text-[var(--color-muted)] transition-transform duration-[var(--duration-short)]",
            open && "rotate-180",
          )}
        />
      </button>

      {open ? (
        <div className="border-t border-[var(--color-border)] bg-[var(--color-raised)] px-5 py-4">
          <div className="grid gap-5 md:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
            <div>
              <p className="text-micro text-[var(--color-muted)]">
                Triggers and weights
              </p>
              <ul className="mt-2 space-y-2">
                {pathway.triggers.map((trigger, index) => (
                  <li
                    key={`${trigger.signal_label}-${index}`}
                    className="flex items-start gap-2.5 text-small"
                  >
                    <span className="mt-0.5 w-8 shrink-0 font-mono text-[0.6875rem] tabular text-[var(--color-accent)]">
                      ×{trigger.weight}
                    </span>
                    <span className="min-w-0">
                      {trigger.description}
                      <span className="ml-1 font-mono text-[0.6875rem] text-[var(--color-muted)]">
                        [{trigger.signal_label}{" "}
                        {trigger.comparison === "at_least" ? "≥" : "≤"}{" "}
                        {trigger.threshold}
                        {trigger.unit ? ` ${trigger.unit}` : ""}]
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-micro text-[var(--color-muted)]">
                  Preconditions
                </p>
                <p className="mt-1.5 text-small">
                  {pathway.gate.is_unconditional
                    ? "Applies year-round in every district."
                    : [
                        pathway.gate.permitted_seasons.length === 1
                          ? `${pathway.gate.permitted_seasons[0] === "dry" ? "Dry" : "Wet"} season only`
                          : null,
                        pathway.gate.requires_meningitis_belt
                          ? "Meningitis-belt districts only"
                          : null,
                        pathway.gate.requires_flood_prone
                          ? "Flood-prone districts only"
                          : null,
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                </p>
              </div>

              <div>
                <p className="text-micro text-[var(--color-muted)]">
                  Agencies with a mandate
                </p>
                <p className="mt-1.5 text-small">
                  {pathway.lead_agencies.length > 0 ? (
                    <>
                      <span className="text-[var(--color-accent)]">Lead</span>{" "}
                      {pathway.lead_agencies.join(", ")}
                    </>
                  ) : null}
                  {pathway.supporting_agencies.length > 0 ? (
                    <>
                      {pathway.lead_agencies.length > 0 ? " · " : null}
                      <span className="text-[var(--color-muted)]">
                        Support
                      </span>{" "}
                      {pathway.supporting_agencies.join(", ")}
                    </>
                  ) : null}
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </li>
  );
}

const DRIVER_ICONS: Record<string, LucideIcon> = {
  rain_flood: CloudRain,
  extreme_heat: Sun,
  harmattan_dust: Wind,
  air_pollution: Factory,
  drought: Sprout,
};

function DriverIcon({ driver }: { driver: string }) {
  const Icon = DRIVER_ICONS[driver] ?? CloudRain;
  return (
    <Icon
      aria-hidden
      strokeWidth={2}
      className="size-4 text-[var(--color-muted)]"
    />
  );
}
