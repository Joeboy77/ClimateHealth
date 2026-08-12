"use client";

import { useQuery } from "@tanstack/react-query";
import { HeartHalf, Phone, SealCheck } from "@phosphor-icons/react";

import { RequireSession } from "@/components/shell/require-session";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import type { GuardianStanding } from "@/lib/api/types";
import { useAuthenticatedSession } from "@/lib/auth/session";
import { cn } from "@/lib/cn";

const POINTS_PER_YEAR = 3500;
/** Within one good week of daily use. These are the people to have an answer ready for. */
const NEARLY_THERE = 0.8;

export default function RenewalsPage() {
  return (
    <RequireSession>
      <RenewalQueue />
    </RequireSession>
  );
}

function RenewalQueue() {
  const { token, user } = useAuthenticatedSession();

  const standings = useQuery({
    queryKey: ["guardian-standings", user?.scope.district_id],
    queryFn: () =>
      api.guardianStandings(token, user?.scope.district_id ?? undefined),
    enabled: token !== "",
  });

  const isGhs = user?.agency.code === "ghs";

  if (!isGhs) {
    return (
      <div className="mx-auto max-w-[1600px] px-6 py-6">
        <header className="border-b border-[var(--color-border)] pb-6">
          <p className="text-eyebrow text-[var(--color-muted)]">
            NHIS renewals
          </p>
          <h1 className="mt-2 max-w-3xl text-display">
            This queue is held by Ghana Health Service
          </h1>
          <p className="mt-2.5 text-small text-[var(--color-muted)]">
            It lists Guardians by name and phone number so an officer can
            arrange a renewal, which is not something every agency needs on
            screen.
          </p>
        </header>
      </div>
    );
  }

  const rows = standings.data ?? [];
  const ready = rows.filter((row) => row.points >= POINTS_PER_YEAR);
  const nearly = rows.filter(
    (row) =>
      row.points < POINTS_PER_YEAR &&
      row.points >= POINTS_PER_YEAR * NEARLY_THERE,
  );

  return (
    <div className="mx-auto max-w-[1600px] space-y-6 px-6 py-6">
      <header className="border-b border-[var(--color-border)] pb-7">
        <div className="flex flex-wrap items-end justify-between gap-x-10 gap-y-5">
          <div className="min-w-0 max-w-3xl">
            <p className="text-eyebrow text-[var(--color-muted)]">
              NHIS renewals earned by Guardians
            </p>
            <h1 className="mt-3 text-statement text-[var(--color-ink)]">
              <span style={{ color: "var(--color-accent)" }}>
                {ready.length}
              </span>
              <span className="text-[var(--color-muted)]">/{rows.length}</span>{" "}
              ready
            </h1>
            <p className="mt-2 text-h1 font-normal text-[var(--color-muted)]">
              have earned a year of cover
            </p>
          </div>

          <dl className="flex shrink-0 divide-x divide-[var(--color-border)]">
            <div className="pr-6">
              <dd className="text-figure">{nearly.length}</dd>
              <dt className="mt-1.5 text-eyebrow text-[var(--color-muted)]">
                nearly there
              </dt>
            </div>
            <div className="px-6">
              <dd className="text-figure">
                {POINTS_PER_YEAR.toLocaleString()}
              </dd>
              <dt className="mt-1.5 text-eyebrow text-[var(--color-muted)]">
                points per year
              </dt>
            </div>
            <div className="pl-6">
              <dd className="text-h1 tabular">GHS 35</dd>
              <dt className="mt-1.5 text-eyebrow text-[var(--color-muted)]">
                adult premium
              </dt>
            </div>
          </dl>
        </div>
      </header>

      <Card>
        <CardHeader
          title="Who to renew next"
          description="Ranked by points earned. A Guardian reaches a year at 3,500."
        />
        {standings.isPending ? (
          <CardBody>
            <Skeleton className="h-64 w-full" />
          </CardBody>
        ) : rows.length === 0 ? (
          <CardBody>
            <p className="text-small text-[var(--color-muted)]">
              No Guardian in your scope has earned points yet.
            </p>
          </CardBody>
        ) : (
          <ul>
            {rows.map((row, index) => (
              <StandingRow key={row.user_id} standing={row} rank={index + 1} />
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function StandingRow({
  standing,
  rank,
}: {
  standing: GuardianStanding;
  rank: number;
}) {
  const ready = standing.points >= POINTS_PER_YEAR;
  const nearly = !ready && standing.points >= POINTS_PER_YEAR * NEARLY_THERE;

  return (
    <li className="flex items-center gap-3.5 border-b border-[var(--color-border)] px-5 py-3.5 last:border-b-0">
      <span className="w-7 shrink-0 font-mono text-[0.6875rem] tabular text-[var(--color-muted)]">
        {rank}
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-x-2.5">
          <span className="text-h3">{standing.display_name}</span>
          {standing.is_minor ? (
            <span className="text-[0.6875rem] text-[var(--color-muted)]">
              under 18, already exempt
            </span>
          ) : null}
        </div>
        <p className="mt-1 flex flex-wrap items-center gap-x-3 text-[0.6875rem] text-[var(--color-muted)]">
          <span>{standing.district_id}</span>
          {standing.phone_number ? (
            <span className="flex items-center gap-1 font-mono">
              <Phone aria-hidden className="size-3" />
              {standing.phone_number}
            </span>
          ) : null}
          {standing.streak_days > 0 ? (
            <span>{standing.streak_days} day streak</span>
          ) : null}
        </p>

        <div className="mt-2 flex items-center gap-2.5">
          <div
            role="progressbar"
            aria-valuenow={standing.percent_of_a_year}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${standing.display_name}: ${standing.percent_of_a_year} per cent of a year`}
            className="h-1.5 max-w-xs flex-1 overflow-hidden rounded-full bg-[var(--color-border)]"
          >
            <div
              className="h-full rounded-full"
              style={{
                width: `${standing.percent_of_a_year}%`,
                backgroundColor: ready
                  ? "var(--color-risk-low)"
                  : nearly
                    ? "var(--color-accent)"
                    : "var(--color-border-strong)",
              }}
            />
          </div>
          <span className="text-[0.6875rem] tabular text-[var(--color-muted)]">
            {standing.points.toLocaleString()} /{" "}
            {POINTS_PER_YEAR.toLocaleString()}
          </span>
        </div>
      </div>

      <span
        className={cn(
          "flex shrink-0 items-center gap-1 rounded-[var(--radius-sm)] border px-2 py-1 text-[0.6875rem]",
          ready
            ? "border-[var(--color-risk-low)]/40 text-[var(--color-risk-low)]"
            : nearly
              ? "border-[var(--color-accent)]/40 text-[var(--color-accent)]"
              : "border-[var(--color-border)] text-[var(--color-muted)]",
        )}
      >
        {ready ? (
          <>
            <SealCheck aria-hidden className="size-3" />A year earned
          </>
        ) : nearly ? (
          <>
            <HeartHalf aria-hidden className="size-3" />
            {standing.points_remaining} to go
          </>
        ) : (
          <>{standing.points_remaining} to go</>
        )}
      </span>
    </li>
  );
}
