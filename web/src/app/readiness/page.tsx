"use client";

import { useQuery } from "@tanstack/react-query";
import { MessageSquareWarning } from "lucide-react";

import { ScopedDistrictPage } from "@/components/district/scoped-district-page";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import type { ReadinessStatus } from "@/lib/api/types";
import { cn } from "@/lib/cn";

const STATUS_COLOUR: Record<ReadinessStatus, string> = {
  ready: "var(--color-risk-low)",
  stretched: "var(--color-risk-moderate)",
  critical: "var(--color-risk-high)",
  emergency: "var(--color-risk-severe)",
};

const STATUS_LABEL: Record<ReadinessStatus, string> = {
  ready: "Ready",
  stretched: "Stretched",
  critical: "Critical",
  emergency: "Emergency",
};

function dispatchDeadline(hours: number | null | undefined): string | null {
  if (hours === null || hours === undefined) return null;
  if (hours === 0) return "cases are already due";
  if (hours < 48) return `${hours}h to move stock`;
  return `${Math.round(hours / 24)}d to move stock`;
}

export default function ReadinessPage() {
  return (
    <ScopedDistrictPage
      title="Resource readiness"
      description="Required units scale with the district's risk level."
    >
      {({ token, districtId }) => (
        <Readiness token={token} districtId={districtId} />
      )}
    </ScopedDistrictPage>
  );
}

function Readiness({
  token,
  districtId,
}: {
  token: string;
  districtId: string;
}) {
  const readiness = useQuery({
    queryKey: ["readiness", districtId],
    queryFn: () => api.readiness(token, districtId),
  });

  if (readiness.isPending) return <Skeleton className="h-64 w-full" />;
  if (readiness.isError) {
    return (
      <p className="text-small text-[var(--color-muted)]">
        {readiness.error.message}
      </p>
    );
  }

  const report = readiness.data;

  return (
    <Card>
      <CardHeader
        title={`${report.district_name} stock against demand`}
        description={[
          `Overall: ${STATUS_LABEL[report.status]}`,
          dispatchDeadline(report.hours_to_dispatch),
        ]
          .filter(Boolean)
          .join(" · ")}
        action={
          <span className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-small text-[var(--color-muted)]">
              <MessageSquareWarning
                aria-hidden
                strokeWidth={2}
                className="size-3.5"
              />
              {report.open_reports} reports
            </span>
            <RiskBadge level={report.overall_risk_level} size="sm" />
          </span>
        }
      />
      {report.resources.length === 0 ? (
        <CardBody>
          <p className="text-small text-[var(--color-muted)]">
            No stock records for this district.
          </p>
        </CardBody>
      ) : (
        <ul>
          {report.resources.map((resource) => {
            const coverage =
              resource.required_units === 0
                ? 1
                : Math.min(resource.stocked_units / resource.required_units, 1);
            const shortfall = resource.shortfall_units;
            const deadline = dispatchDeadline(resource.hours_to_dispatch);
            return (
              <li
                key={resource.resource}
                className="border-b border-[var(--color-border)] px-5 py-3.5 last:border-b-0"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="text-small font-medium">
                    {resource.resource}
                  </span>
                  <span className="font-mono text-[0.75rem] tabular text-[var(--color-muted)]">
                    {resource.stocked_units} of {resource.required_units} units
                    {shortfall > 0 ? (
                      <span
                        className="ml-2 font-medium"
                        style={{ color: STATUS_COLOUR[resource.status] }}
                      >
                        short {shortfall}
                        {deadline ? ` · ${deadline}` : ""}
                      </span>
                    ) : null}
                  </span>
                </div>
                <div className="mt-2 flex items-center gap-3">
                  <span className="h-1.5 flex-1 rounded-[var(--radius-sm)] bg-[var(--color-border)]">
                    <span
                      className="block h-full rounded-[var(--radius-sm)] transition-all duration-[var(--duration-medium)]"
                      style={{
                        width: `${coverage * 100}%`,
                        backgroundColor: STATUS_COLOUR[resource.status],
                      }}
                    />
                  </span>
                  <span
                    className={cn("w-20 shrink-0 text-right text-[0.6875rem]")}
                    style={{ color: STATUS_COLOUR[resource.status] }}
                  >
                    {STATUS_LABEL[resource.status]}
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}
