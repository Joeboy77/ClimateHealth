"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ChevronDown, Users } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { DistrictPreventionCard } from "@/components/prevention/district-prevention-card";
import { CommunitySignalsPanel } from "@/components/district/community-signals";
import { DataSourceControl } from "@/components/district/data-source-control";
import { DistrictMap } from "@/components/map/district-map";
import { RequireSession } from "@/components/shell/require-session";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import type {
  ClimateSnapshot,
  ConfidenceMode,
  DistrictDetail,
  Risk,
} from "@/lib/api/types";
import { conditionLabel } from "@/lib/api/types";
import { useAuthenticatedSession } from "@/lib/auth/session";
import { cn } from "@/lib/cn";
import {
  CONFIDENCE_COPY,
  CONFIDENCE_SHORT,
  CONFIDENCE_TIER,
  SCORE_EXPLANATION,
  formatScore,
  lagWindowText,
  relativeDay,
  riskPresentation,
} from "@/lib/risk";

export default function DistrictDetailPage() {
  return (
    <RequireSession>
      <DistrictDetailView />
    </RequireSession>
  );
}

function DistrictDetailView() {
  const { token, user } = useAuthenticatedSession();
  const params = useParams<{ districtId: string }>();
  const showNationalLink = user?.scope.level === "national";
  const districtId = params.districtId;

  const district = useQuery({
    queryKey: ["district", districtId],
    queryFn: () => api.district(token, districtId),
  });

  const forecast = useQuery({
    queryKey: ["forecast", districtId],
    queryFn: () => api.forecast(token, districtId),
  });

  const reports = useQuery({
    queryKey: ["reports", districtId],
    queryFn: () => api.reports(token, districtId),
  });

  if (district.isPending) {
    return (
      <div className="space-y-5 px-6 py-6">
        <Skeleton className="h-16 w-72" />
        <Skeleton className="h-[420px] w-full" />
      </div>
    );
  }

  if (district.isError) {
    return (
      <div className="px-6 py-6">
        {showNationalLink ? <BackLink /> : null}
        <p className="mt-4 text-small text-[var(--color-muted)]">
          {district.error.message}
        </p>
      </div>
    );
  }

  const detail = district.data;

  return (
    <div className="px-6 py-6">
      {showNationalLink ? <BackLink /> : null}

      <header
        className={cn(
          "flex flex-wrap items-start justify-between gap-4",
          showNationalLink && "mt-3",
        )}
      >
        <div>
          <h1 className="text-h1">{detail.name}</h1>
          <p className="mt-1 text-small text-[var(--color-muted)]">
            {detail.region} ·{" "}
            {detail.season === "dry" ? "Dry season" : "Wet season"} · climate
            observed {relativeDay(detail.climate.observed_on)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ProvenanceChip snapshot={detail.climate} />
          <RiskBadge level={detail.overall_risk_level} />
        </div>
      </header>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <Card>
          <CardHeader
            title="Ranked health risks"
            description="Decided by published thresholds. Expand a row for the conditions that fired."
          />
          {detail.risks.length === 0 ? (
            <CardBody>
              <p className="text-small text-[var(--color-muted)]">
                No pathway applies to this district under current conditions.
              </p>
            </CardBody>
          ) : (
            <ul>
              {detail.risks.map((risk) => (
                <RiskRow key={risk.condition} risk={risk} />
              ))}
            </ul>
          )}
        </Card>

        <div className="space-y-5">
          <Card className="overflow-hidden">
            <CardHeader
              title={`${detail.name} district`}
              description="Boundary from geoBoundaries. Pins are community reports."
            />
            <div className="aspect-[23/20] bg-[var(--color-canvas)] p-2">
              <DistrictMap
                districtId={detail.district_id}
                districtName={detail.name}
                level={detail.overall_risk_level}
                centre={{
                  latitude: detail.latitude,
                  longitude: detail.longitude,
                }}
                reports={reports.data ?? []}
                className="h-full w-full"
              />
            </div>
          </Card>

          <DataSourceControl
            token={token}
            districtId={detail.district_id}
            provenance={detail.climate.provenance}
            observedOn={detail.climate.observed_on}
          />

          <Card>
            <CardHeader
              title="Citizen forecast"
              description="Phrased from the engine's decision."
            />
            <CardBody>
              {forecast.isPending ? (
                <div className="space-y-2">
                  <Skeleton className="h-5 w-3/4" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : forecast.isError ? (
                <p className="text-small text-[var(--color-muted)]">
                  {forecast.error.message}
                </p>
              ) : (
                <>
                  <p className="text-h2">{forecast.data.headline}</p>
                  <p className="mt-2 text-small text-[var(--color-muted)]">
                    {forecast.data.summary}
                  </p>
                  <div className="mt-4 rounded-[var(--radius-md)] border border-[var(--color-accent)]/25 bg-[var(--color-accent-subtle)] px-3.5 py-3">
                    <p className="text-micro text-[var(--color-accent)]">
                      Action for today
                    </p>
                    <p className="mt-1 text-small text-[var(--color-ink)]">
                      {forecast.data.action_today}
                    </p>
                  </div>
                </>
              )}
            </CardBody>
          </Card>

          <DistrictPreventionCard
            token={token}
            districtId={detail.district_id}
          />

          <CommunitySignalsPanel signals={detail.community_signals} />

          <ClimateCard snapshot={detail.climate} />
        </div>
      </div>
    </div>
  );
}

function BackLink() {
  return (
    <Link
      href="/"
      className="inline-flex items-center gap-1.5 text-small text-[var(--color-muted)] transition-colors duration-[var(--duration-instant)] hover:text-[var(--color-ink)]"
    >
      <ArrowLeft aria-hidden strokeWidth={2} className="size-3.5" />
      National risk picture
    </Link>
  );
}

function ProvenanceChip({ snapshot }: { snapshot: ClimateSnapshot }) {
  const simulated = snapshot.provenance === "demo";
  return (
    <span
      className={cn(
        "rounded-[var(--radius-sm)] border px-2 py-1 text-xs",
        simulated
          ? "border-[var(--color-confidence-demo)]/30 bg-[var(--color-confidence-demo-surface)] text-[var(--color-confidence-demo)]"
          : "border-[var(--color-border)] bg-[var(--color-raised)] text-[var(--color-muted)]",
      )}
    >
      {simulated ? "Simulated readings" : "Live Open-Meteo readings"}
    </span>
  );
}

/** Proposal section 6.3: every risk declares the tier that produced it. */
function TierChip({ mode }: { mode: ConfidenceMode }) {
  const baseline = mode === "baseline";
  return (
    <span
      title={CONFIDENCE_COPY[mode]}
      className={cn(
        "rounded-[var(--radius-sm)] border px-1.5 py-0.5 text-[0.625rem] font-medium uppercase tracking-wide",
        baseline
          ? "border-[var(--color-risk-moderate)]/40 border-dashed text-[var(--color-risk-moderate)]"
          : "border-[var(--color-border)] text-[var(--color-muted)]",
      )}
    >
      {CONFIDENCE_TIER[mode]} · {CONFIDENCE_SHORT[mode]}
    </span>
  );
}

function RiskRow({ risk }: { risk: Risk }) {
  const [expanded, setExpanded] = useState(false);
  const { icon: Icon, foreground } = riskPresentation(risk.level);

  return (
    <li className="border-b border-[var(--color-border)] last:border-b-0">
      <button
        type="button"
        onClick={() => setExpanded((open) => !open)}
        aria-expanded={expanded}
        className="flex w-full items-center gap-4 px-5 py-3.5 text-left transition-colors duration-[var(--duration-instant)] hover:bg-[var(--color-raised)]"
      >
        <Icon
          aria-hidden
          strokeWidth={2}
          className={cn("size-4 shrink-0", foreground)}
        />

        <span className="min-w-0 flex-1">
          <span className="block text-h3">
            {conditionLabel(risk.condition)}
          </span>
          <span className="mt-0.5 flex items-center gap-1.5 text-[0.75rem] text-[var(--color-muted)]">
            <Users aria-hidden strokeWidth={2} className="size-3" />
            {risk.vulnerable_group}
          </span>
        </span>

        <LagWindowScale risk={risk} />

        <span className="w-12 shrink-0 text-right">
          <span
            title={SCORE_EXPLANATION}
            className={cn("font-mono text-small tabular", foreground)}
          >
            {formatScore(risk.score)}
          </span>
        </span>

        <TierChip mode={risk.confidence} />
        <RiskBadge level={risk.level} size="sm" showIcon={false} />

        <ChevronDown
          aria-hidden
          strokeWidth={2}
          className={cn(
            "size-4 shrink-0 text-[var(--color-muted)] transition-transform duration-[var(--duration-short)]",
            expanded && "rotate-180",
          )}
        />
      </button>

      {expanded ? (
        <div className="border-t border-[var(--color-border)] bg-[var(--color-raised)] px-5 py-4">
          <p className="text-micro text-[var(--color-muted)]">
            {risk.reasons.length > 0
              ? "Conditions that triggered this"
              : "No trigger fired"}
          </p>
          {risk.reasons.length > 0 ? (
            <ul className="mt-2 space-y-1.5">
              {risk.reasons.map((reason) => (
                <li key={reason} className="flex gap-2.5 text-small">
                  <span
                    aria-hidden
                    className={cn(
                      "mt-1.5 size-1.5 shrink-0 rounded-[var(--radius-sm)]",
                      riskPresentation(risk.level).dot,
                    )}
                  />
                  {reason}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1.5 text-small text-[var(--color-muted)]">
              This pathway applies here, but no climate threshold has been
              crossed.
            </p>
          )}
        </div>
      ) : null}
    </li>
  );
}

const LAG_SCALE_DAYS = 60;

function LagWindowScale({ risk }: { risk: Risk }) {
  const { minimum_days: start, maximum_days: end } = risk.lag_window;
  const left = Math.min((start / LAG_SCALE_DAYS) * 100, 96);
  const width = Math.max(
    Math.min(((end - start) / LAG_SCALE_DAYS) * 100, 100 - left),
    4,
  );

  return (
    <span className="hidden w-40 shrink-0 md:block">
      <span className="block text-[0.6875rem] text-[var(--color-muted)]">
        cases in {lagWindowText(risk.lag_window)}
      </span>
      <span className="mt-1 block h-1.5 w-full rounded-[var(--radius-sm)] bg-[var(--color-border)]">
        <span
          className="block h-full rounded-[var(--radius-sm)]"
          style={{
            marginLeft: `${left}%`,
            width: `${width}%`,
            backgroundColor: `var(--color-risk-${risk.level})`,
          }}
        />
      </span>
    </span>
  );
}

const CLIMATE_READINGS = [
  { key: "rainfall_7d_mm", label: "Rainfall, 7 days", unit: "mm" },
  { key: "rainfall_14d_mm", label: "Rainfall, 14 days", unit: "mm" },
  { key: "consecutive_dry_days", label: "Consecutive dry days", unit: "days" },
  { key: "humidity_mean_percent", label: "Average humidity", unit: "%" },
  { key: "temperature_mean_c", label: "Average temperature", unit: "°C" },
  { key: "temperature_max_c", label: "Peak temperature", unit: "°C" },
  { key: "dust_concentration_ug_m3", label: "Dust", unit: "µg/m³" },
  { key: "particulate_matter_10_ug_m3", label: "PM10", unit: "µg/m³" },
] as const;

function ClimateCard({ snapshot }: { snapshot: ClimateSnapshot }) {
  return (
    <Card>
      <CardHeader
        title="Climate snapshot"
        description="The readings the engine evaluated."
      />
      <CardBody className="grid grid-cols-2 gap-x-5 gap-y-3.5">
        {CLIMATE_READINGS.map(({ key, label, unit }) => {
          const value = snapshot[key as keyof ClimateSnapshot];
          const missing = value === null || value === undefined;
          return (
            <div key={key}>
              <p className="text-[0.6875rem] text-[var(--color-muted)]">
                {label}
              </p>
              <p className="mt-0.5 font-mono text-small tabular text-[var(--color-ink)]">
                {missing ? (
                  <span className="text-[var(--color-muted)]">
                    not reported
                  </span>
                ) : (
                  <>
                    {typeof value === "number"
                      ? Math.round(value * 10) / 10
                      : value}
                    <span className="ml-1 text-[var(--color-muted)]">
                      {unit}
                    </span>
                  </>
                )}
              </p>
            </div>
          );
        })}
      </CardBody>
    </Card>
  );
}

export type { DistrictDetail };
