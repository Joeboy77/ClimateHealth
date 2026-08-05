"use client";

import { ShieldCheck } from "lucide-react";

import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { PreventionLeaderboard } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import {
  AVERTED_EXPLANATION,
  DISTINCTION,
  onTimePercentage,
} from "@/lib/prevention";

const LISTED_DISTRICTS = 6;

export function PreventionPanel({
  leaderboard,
  loading,
  onOpenDistrict,
}: {
  leaderboard: PreventionLeaderboard | undefined;
  loading: boolean;
  onOpenDistrict: (districtId: string) => void;
}) {
  const rated = (leaderboard?.records ?? []).filter(
    (record) => record.actions_total > 0,
  );

  return (
    <Card>
      <CardHeader
        title="Prevention record"
        description="Standing earned from the action log, not self-reported."
        action={
          <span
            className="font-mono text-small tabular text-[var(--color-risk-low)]"
            title={AVERTED_EXPLANATION}
          >
            {leaderboard?.outbreaks_averted ?? 0} averted
          </span>
        }
      />
      {loading ? (
        <CardBody className="space-y-2">
          {Array.from({ length: 4 }, (_, index) => (
            <Skeleton key={index} className="h-10 w-full" />
          ))}
        </CardBody>
      ) : rated.length === 0 ? (
        <CardBody className="flex items-start gap-3">
          <ShieldCheck
            aria-hidden
            strokeWidth={2}
            className="mt-0.5 size-4 shrink-0 text-[var(--color-muted)]"
          />
          <p className="text-small text-[var(--color-muted)]">
            No district has a mandated action on record yet. A standing appears
            once the engine raises a hazard and the agencies work their tasks.
          </p>
        </CardBody>
      ) : (
        <ul>
          {rated.slice(0, LISTED_DISTRICTS).map((record) => {
            const badge = DISTINCTION[record.distinction];
            return (
              <li key={record.district_id}>
                <button
                  type="button"
                  onClick={() => onOpenDistrict(record.district_id)}
                  className={cn(
                    "flex w-full items-center gap-3 border-b border-[var(--color-border)] px-5 py-2.5 text-left",
                    "transition-colors duration-[var(--duration-instant)] last:border-b-0",
                    "hover:bg-[var(--color-raised)]",
                  )}
                >
                  <span
                    aria-hidden
                    className="size-1.5 shrink-0 rounded-full"
                    style={{ backgroundColor: badge.cssVariable }}
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-small text-[var(--color-ink)]">
                      {record.district_name}
                    </span>
                    <span className="block truncate text-[0.6875rem] text-[var(--color-muted)]">
                      {record.actions_on_time} of {record.actions_total} closed
                      before onset
                      {record.actions_overdue > 0
                        ? ` · ${record.actions_overdue} overdue`
                        : ""}
                    </span>
                  </span>
                  <span
                    title={badge.meaning}
                    className="shrink-0 text-[0.6875rem]"
                    style={{ color: badge.cssVariable }}
                  >
                    {badge.label}
                  </span>
                  <span className="w-10 shrink-0 text-right font-mono text-[0.75rem] tabular text-[var(--color-muted)]">
                    {onTimePercentage(record.on_time_rate)}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}
