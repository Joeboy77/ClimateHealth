"use client";

import { ArrowUpRight, Crosshair } from "@phosphor-icons/react";

import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AGENCY_PRESENTATION } from "@/lib/agencies";
import type { AgencyOverview } from "@/lib/api/types";
import { conditionLabel } from "@/lib/api/types";
import { cn } from "@/lib/cn";

/**
 * Proposal section 8: every agency gets a role-based view of the same shared risk
 * picture. This panel narrows the national picture to the conditions this agency
 * actually answers for, and says which of them it leads.
 */
export function AgencyLens({
  overview,
  loading,
  onOpenDistrict,
}: {
  overview: AgencyOverview | undefined;
  loading: boolean;
  onOpenDistrict: (districtId: string) => void;
}) {
  if (loading || !overview) {
    return <Skeleton className="h-64 w-full" />;
  }

  const presentation = AGENCY_PRESENTATION[overview.agency];
  const AgencyIcon = presentation.icon;

  return (
    <Card>
      <CardHeader
        title={`${overview.agency_short_name} remit`}
        description={overview.remit}
        action={
          <span
            aria-hidden
            className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] border"
            style={{
              borderColor: presentation.colour,
              color: presentation.colour,
            }}
          >
            <AgencyIcon className="size-4" />
          </span>
        }
      />
      <CardBody className="space-y-4">
        <p className="flex items-start gap-2 text-small">
          <Crosshair
            aria-hidden
            className="mt-0.5 size-4 shrink-0 text-[var(--color-muted)]"
          />
          {overview.leading_question}
        </p>

        <p className="text-small text-[var(--color-muted)]">
          <span
            className="text-metric"
            style={{
              color:
                overview.districts_needing_action > 0
                  ? presentation.colour
                  : "var(--color-muted)",
            }}
          >
            {overview.districts_needing_action}
          </span>{" "}
          of {overview.districts_in_scope} districts need{" "}
          {overview.agency_short_name} action
        </p>

        {overview.exposures.length === 0 ? (
          <p className="text-small text-[var(--color-muted)]">
            Nothing in your remit is raised right now. Conditions you hold a
            mandate for appear here the moment they cross high risk.
          </p>
        ) : (
          <ul className="space-y-1">
            {overview.exposures.map((exposure) => (
              <li key={exposure.condition}>
                <button
                  type="button"
                  onClick={() => onOpenDistrict(exposure.worst_district_id)}
                  className={cn(
                    "group flex w-full items-center gap-3 rounded-[var(--radius-md)] px-2 py-2 text-left",
                    "transition-colors duration-[var(--duration-instant)] hover:bg-[var(--color-raised)]",
                  )}
                >
                  <span
                    className="w-11 shrink-0 rounded-[var(--radius-sm)] border px-1 py-0.5 text-center text-[0.625rem] font-semibold uppercase"
                    style={
                      exposure.is_lead
                        ? {
                            borderColor: presentation.colour,
                            color: presentation.colour,
                          }
                        : {
                            borderColor: "var(--color-border)",
                            color: "var(--color-muted)",
                          }
                    }
                  >
                    {exposure.is_lead ? "Lead" : "Supp"}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-small font-medium">
                      {conditionLabel(exposure.condition)}
                    </span>
                    <span className="block truncate text-[0.6875rem] text-[var(--color-muted)]">
                      {exposure.districts_raised} districts · worst in{" "}
                      {exposure.worst_district_name}
                    </span>
                  </span>
                  <RiskBadge
                    level={exposure.worst_level}
                    size="sm"
                    showIcon={false}
                  />
                  <ArrowUpRight
                    aria-hidden
                    className="size-3.5 shrink-0 text-[var(--color-muted)] opacity-0 transition-opacity duration-[var(--duration-instant)] group-hover:opacity-100"
                  />
                </button>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}
