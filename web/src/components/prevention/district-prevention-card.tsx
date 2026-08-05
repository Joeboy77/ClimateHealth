"use client";

import { useQuery } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";

import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import { conditionLabel } from "@/lib/api/types";
import {
  AVERTED_EXPLANATION,
  DISTINCTION,
  onTimePercentage,
} from "@/lib/prevention";

export function DistrictPreventionCard({
  token,
  districtId,
}: {
  token: string;
  districtId: string;
}) {
  const record = useQuery({
    queryKey: ["prevention", districtId],
    queryFn: () => api.preventionRecord(token, districtId),
  });

  const badge = record.data ? DISTINCTION[record.data.distinction] : null;

  return (
    <Card>
      <CardHeader
        title="Prevention record"
        description="Earned from this district's action log."
        action={
          badge ? (
            <span
              title={badge.meaning}
              className="text-[0.6875rem]"
              style={{ color: badge.cssVariable }}
            >
              {badge.label}
            </span>
          ) : null
        }
      />
      <CardBody>
        {record.isPending ? (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-5 w-2/3" />
          </div>
        ) : record.isError ? (
          <p className="text-small text-[var(--color-muted)]">
            {record.error.message}
          </p>
        ) : (
          <>
            <div className="grid grid-cols-3 gap-4">
              <Figure
                label="Closed before onset"
                value={onTimePercentage(record.data.on_time_rate)}
              />
              <Figure
                label="Actions on record"
                value={String(record.data.actions_total)}
              />
              <Figure
                label="Overdue now"
                value={String(record.data.actions_overdue)}
                tone={
                  record.data.actions_overdue > 0
                    ? "var(--color-risk-high)"
                    : undefined
                }
              />
            </div>

            {record.data.averted_hazards.length === 0 ? (
              <p className="mt-4 text-small text-[var(--color-muted)]">
                No hazard yet has every mandated lead action closed inside its
                onset window.
              </p>
            ) : (
              <div className="mt-4">
                <p
                  className="flex items-center gap-1.5 text-micro text-[var(--color-risk-low)]"
                  title={AVERTED_EXPLANATION}
                >
                  <ShieldCheck
                    aria-hidden
                    strokeWidth={2}
                    className="size-3.5"
                  />
                  {record.data.averted_hazards.length} hazard
                  {record.data.averted_hazards.length === 1 ? "" : "s"} met in
                  full
                </p>
                <ul className="mt-2 space-y-1.5">
                  {record.data.averted_hazards.map((hazard) => (
                    <li
                      key={hazard.condition}
                      className="flex items-baseline justify-between gap-3 text-small"
                    >
                      <span>{conditionLabel(hazard.condition)}</span>
                      <span className="shrink-0 text-[0.6875rem] text-[var(--color-muted)]">
                        {hazard.lead_actions} lead action
                        {hazard.lead_actions === 1 ? "" : "s"} · closed{" "}
                        {hazard.closed_on}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </CardBody>
    </Card>
  );
}

function Figure({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: string;
}) {
  return (
    <div>
      <p className="text-[0.6875rem] text-[var(--color-muted)]">{label}</p>
      <p
        className="mt-1 text-h2 tabular"
        style={tone ? { color: tone } : undefined}
      >
        {value}
      </p>
    </div>
  );
}
