"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Clock3, Network, ShieldAlert, Users } from "lucide-react";
import Link from "next/link";

import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import type { PublicDistrictRisk } from "@/lib/api/types";
import { conditionLabel } from "@/lib/api/types";
import { RISK_CSS_VARIABLE, formatScore } from "@/lib/risk";

export default function PublicOverviewPage() {
  const overview = useQuery({
    queryKey: ["public-overview"],
    queryFn: () => api.publicOverview(),
  });

  return (
    <div className="mx-auto max-w-[1100px] px-6 py-10">
      <header>
        <p className="text-micro text-[var(--color-muted)]">
          Public warning picture · Ghana
        </p>
        {overview.isPending ? (
          <Skeleton className="mt-3 h-16 w-full max-w-2xl" />
        ) : overview.isError ? (
          <p className="mt-3 text-small text-[var(--color-muted)]">
            {overview.error.message}
          </p>
        ) : (
          <>
            <h1 className="mt-2 max-w-3xl text-display">
              <span
                style={{
                  color:
                    RISK_CSS_VARIABLE[
                      overview.data.districts[0]?.level ?? "low"
                    ],
                }}
              >
                {overview.data.districts_raised}
              </span>{" "}
              of {overview.data.districts_assessed} districts have a health risk
              rising now
            </h1>
            <p className="mt-3 max-w-2xl text-small text-[var(--color-muted)]">
              Computed today from open weather observations against published
              epidemiological thresholds. No account needed: you cannot act on a
              warning you are not allowed to read. Agency workload and community
              reports stay behind the login.
            </p>
          </>
        )}
      </header>

      {overview.data ? (
        <>
          <section className="mt-8">
            <h2 className="text-micro text-[var(--color-muted)]">
              What is rising, and where
            </h2>
            <ul className="mt-3 flex flex-wrap gap-2.5">
              {overview.data.conditions.map((entry) => (
                <li
                  key={entry.condition}
                  className="flex items-baseline gap-2 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2"
                >
                  <span
                    aria-hidden
                    className="size-1.5 rounded-full"
                    style={{
                      backgroundColor: RISK_CSS_VARIABLE[entry.worst_level],
                    }}
                  />
                  <span className="text-small">
                    {conditionLabel(entry.condition)}
                  </span>
                  <span className="font-mono text-[0.75rem] tabular text-[var(--color-muted)]">
                    {entry.districts_raised}
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <Card className="mt-6">
            <CardHeader
              title="Districts to watch"
              description="Ranked by severity. Each carries the onset window of its leading condition."
            />
            {overview.data.districts.length === 0 ? (
              <CardBody>
                <p className="text-small text-[var(--color-muted)]">
                  No district is above the warning threshold today.
                </p>
              </CardBody>
            ) : (
              <ul>
                {overview.data.districts.map((district) => (
                  <PublicRow key={district.district_id} district={district} />
                ))}
              </ul>
            )}
          </Card>

          <p className="mt-4 text-[0.6875rem] text-[var(--color-muted)]">
            Generated {overview.data.generated_on}. A risk score is the share of
            a pathway&rsquo;s readable trigger weight that fired. It is not a
            probability, and it is not a diagnosis.
          </p>
        </>
      ) : null}

      <div className="mt-8 flex flex-wrap items-center gap-3">
        <Link
          href="/matrix"
          className="inline-flex items-center gap-1.5 rounded-[var(--radius-md)] border border-[var(--color-border)] px-3.5 py-2 text-small transition-colors duration-[var(--duration-instant)] hover:bg-[var(--color-raised)]"
        >
          <Network aria-hidden strokeWidth={2} className="size-3.5" />
          See how every warning is decided
        </Link>
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-small text-[var(--color-accent)] transition-opacity duration-[var(--duration-instant)] hover:opacity-80"
        >
          Agency sign in
          <ArrowRight aria-hidden strokeWidth={2} className="size-3.5" />
        </Link>
      </div>
    </div>
  );
}

function PublicRow({ district }: { district: PublicDistrictRisk }) {
  return (
    <li className="flex items-start gap-3.5 border-b border-[var(--color-border)] px-5 py-3.5 last:border-b-0">
      <span
        aria-hidden
        className="mt-0.5 h-9 w-1 shrink-0 rounded-full"
        style={{ backgroundColor: RISK_CSS_VARIABLE[district.level] }}
      />
      <div className="min-w-0 flex-1">
        <p className="flex flex-wrap items-center gap-2">
          <span className="text-h3">{district.district_name}</span>
          <span className="text-[0.75rem] text-[var(--color-muted)]">
            {district.region}
          </span>
        </p>
        <p className="mt-1 flex flex-wrap items-center gap-x-3.5 gap-y-1 text-[0.75rem] text-[var(--color-muted)]">
          <span className="flex items-center gap-1">
            <ShieldAlert aria-hidden strokeWidth={2} className="size-3" />
            {conditionLabel(district.leading_condition)}
          </span>
          <span className="flex items-center gap-1">
            <Clock3 aria-hidden strokeWidth={2} className="size-3" />
            cases possible in{" "}
            {district.onset_days_minimum === district.onset_days_maximum
              ? `${district.onset_days_minimum} days`
              : `${district.onset_days_minimum}\u2013${district.onset_days_maximum} days`}
          </span>
          <span className="flex items-center gap-1">
            <Users aria-hidden strokeWidth={2} className="size-3" />
            {district.vulnerable_group}
          </span>
        </p>
      </div>
      <span className="shrink-0 font-mono text-small tabular text-[var(--color-muted)]">
        {formatScore(district.score)}
      </span>
      <RiskBadge level={district.level} />
    </li>
  );
}
