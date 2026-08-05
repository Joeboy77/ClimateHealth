"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, BellRing, RefreshCw, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AgencyLens } from "@/components/agency/agency-lens";
import { RiskMap } from "@/components/map/risk-map";
import { RequireSession } from "@/components/shell/require-session";
import { Button } from "@/components/ui/button";
import { PreventionPanel } from "@/components/prevention/prevention-panel";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { Pagination } from "@/components/ui/pagination";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import type { Alert, DistrictSummary, RiskLevel } from "@/lib/api/types";
import { conditionLabel, RISK_LEVEL_RANK } from "@/lib/api/types";
import { useAuthenticatedSession } from "@/lib/auth/session";
import type { ClimateLayerId } from "@/lib/climate-layers";
import { cn } from "@/lib/cn";
import {
  RISK_CSS_VARIABLE,
  formatScore,
  relativeDay,
  riskPresentation,
} from "@/lib/risk";

export default function NationalPicturePage() {
  return (
    <RequireSession>
      <NationalPicture />
    </RequireSession>
  );
}

function NationalPicture() {
  const { token, user } = useAuthenticatedSession();
  const router = useRouter();

  const scopedDistrictId =
    user?.scope.level === "district" ? user.scope.district_id : null;

  useEffect(() => {
    if (scopedDistrictId) router.replace(`/districts/${scopedDistrictId}`);
  }, [scopedDistrictId, router]);

  const districts = useQuery({
    queryKey: ["districts"],
    queryFn: () => api.districts(token),
  });
  const alerts = useQuery({
    queryKey: ["alerts"],
    queryFn: () => api.alerts(token),
  });
  const agency = useQuery({
    queryKey: ["agency-overview"],
    queryFn: () => api.agencyOverview(token),
  });
  const prevention = useQuery({
    queryKey: ["prevention"],
    queryFn: () => api.prevention(token),
  });

  const open = (districtId: string) => router.push(`/districts/${districtId}`);

  const rows = [...(districts.data ?? [])].sort(
    (first, second) =>
      RISK_LEVEL_RANK[second.overall_risk_level] -
        RISK_LEVEL_RANK[first.overall_risk_level] ||
      first.name.localeCompare(second.name),
  );

  if (scopedDistrictId) {
    return (
      <div className="grid min-h-[60vh] place-items-center">
        <p className="text-small text-[var(--color-muted)]">
          Opening your district…
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1600px] px-6 py-6">
      <Lead
        districts={districts.data}
        alerts={alerts.data}
        loading={districts.isPending}
        refreshing={districts.isFetching}
        onRefresh={() => {
          void districts.refetch();
          void alerts.refetch();
        }}
      />

      <div className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,5fr)_minmax(0,4fr)]">
        <Card className="overflow-hidden">
          <CardHeader
            title="Where risk is concentrated"
            description="All 260 districts, coloured by current risk. Hover for detail, click to open."
          />
          <div className="aspect-[31/36] bg-[var(--color-canvas)] p-2">
            {districts.isPending ? (
              <Skeleton className="h-full w-full" />
            ) : (
              <RiskMap
                districts={districts.data ?? []}
                onSelect={open}
                initialLayer={
                  (agency.data?.default_climate_layer as ClimateLayerId) ??
                  "risk"
                }
              />
            )}
          </div>
        </Card>

        <div className="space-y-5">
          <Card>
            <CardHeader
              title="Districts by risk"
              description="Highest first. Select one to open it."
            />
            {districts.isPending ? (
              <CardBody className="space-y-2">
                {Array.from({ length: 7 }, (_, index) => (
                  <Skeleton key={index} className="h-12 w-full" />
                ))}
              </CardBody>
            ) : districts.isError ? (
              <CardBody>
                <p className="text-small text-[var(--color-muted)]">
                  {districts.error.message}
                </p>
                <Button
                  size="sm"
                  className="mt-3"
                  onClick={() => void districts.refetch()}
                >
                  Try again
                </Button>
              </CardBody>
            ) : (
              <DistrictList rows={rows} onOpen={open} />
            )}
          </Card>

          <AgencyLens
            overview={agency.data}
            loading={agency.isPending}
            onOpenDistrict={open}
          />

          <ConditionSpread alerts={alerts.data} loading={alerts.isPending} />

          <PreventionPanel
            leaderboard={prevention.data}
            loading={prevention.isPending}
            onOpenDistrict={open}
          />

          <AlertStream
            alerts={alerts.data}
            loading={alerts.isPending}
            onOpen={open}
          />
        </div>
      </div>
    </div>
  );
}

function Lead({
  districts,
  alerts,
  loading,
  refreshing,
  onRefresh,
}: {
  districts: DistrictSummary[] | undefined;
  alerts: Alert[] | undefined;
  loading: boolean;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  if (loading || !districts) {
    return <Skeleton className="h-24 w-full max-w-3xl" />;
  }

  const elevated = districts.filter(
    (district) => RISK_LEVEL_RANK[district.overall_risk_level] >= 2,
  );
  const severe = districts.filter(
    (district) => district.overall_risk_level === "severe",
  );
  const worst = [...districts].sort(
    (first, second) =>
      RISK_LEVEL_RANK[second.overall_risk_level] -
      RISK_LEVEL_RANK[first.overall_risk_level],
  )[0];

  const tone: RiskLevel =
    severe.length > 0 ? "severe" : elevated.length > 0 ? "high" : "low";

  return (
    <header className="flex flex-wrap items-start justify-between gap-6">
      <div className="min-w-0">
        <p className="text-micro text-[var(--color-muted)]">
          National risk picture
        </p>
        <h1 className="mt-2 max-w-2xl text-display">
          <span style={{ color: RISK_CSS_VARIABLE[tone] }}>
            {elevated.length} of {districts.length} districts
          </span>{" "}
          are at high risk or above
        </h1>
        <p className="mt-2.5 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-small text-[var(--color-muted)]">
          <span>
            {severe.length > 0
              ? `${severe.length} rated severe`
              : "None rated severe"}
          </span>
          <Dot />
          <span>{alerts?.length ?? 0} active alerts</span>
          <Dot />
          <span>
            Climate observed{" "}
            {districts[0] ? relativeDay(districts[0].generated_on) : "today"}
          </span>
          {worst?.leading_condition ? (
            <>
              <Dot />
              <span>
                Leading concern{" "}
                <span className="text-[var(--color-ink)]">
                  {conditionLabel(worst.leading_condition)}
                </span>{" "}
                in {worst.name}
              </span>
            </>
          ) : null}
        </p>
      </div>

      <Button size="sm" onClick={onRefresh} disabled={refreshing}>
        <RefreshCw
          aria-hidden
          strokeWidth={2}
          className={refreshing ? "size-4 animate-spin" : "size-4"}
        />
        Refresh
      </Button>
    </header>
  );
}

function Dot() {
  return (
    <span aria-hidden className="text-[var(--color-border-strong)]">
      ·
    </span>
  );
}

const DISTRICTS_PER_PAGE = 12;

function DistrictList({
  rows,
  onOpen,
}: {
  rows: DistrictSummary[];
  onOpen: (districtId: string) => void;
}) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter(
      (district) =>
        district.name.toLowerCase().includes(needle) ||
        district.region.toLowerCase().includes(needle),
    );
  }, [rows, search]);

  const pageCount = Math.max(
    1,
    Math.ceil(filtered.length / DISTRICTS_PER_PAGE),
  );
  const currentPage = Math.min(page, pageCount);
  const visible = filtered.slice(
    (currentPage - 1) * DISTRICTS_PER_PAGE,
    currentPage * DISTRICTS_PER_PAGE,
  );

  if (rows.length === 0) {
    return (
      <CardBody>
        <p className="text-small text-[var(--color-muted)]">
          No districts are visible to your account.
        </p>
      </CardBody>
    );
  }

  return (
    <>
      <div className="border-b border-[var(--color-border)] px-5 py-2.5">
        <div className="relative">
          <Search
            aria-hidden
            strokeWidth={2}
            className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-[var(--color-muted)]"
          />
          <label htmlFor="district-search" className="sr-only">
            Search districts
          </label>
          <input
            id="district-search"
            type="search"
            value={search}
            placeholder="Search district or region"
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            className="h-8 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] pl-8 pr-3 text-small text-[var(--color-ink)] transition-colors duration-[var(--duration-instant)] placeholder:text-[var(--color-muted)] hover:border-[var(--color-border-strong)]"
          />
        </div>
      </div>

      {visible.length === 0 ? (
        <CardBody>
          <p className="text-small text-[var(--color-muted)]">
            No district matches “{search}”.
          </p>
        </CardBody>
      ) : (
        <ul>
          {visible.map((district, index) => {
            const { icon: Icon, foreground } = riskPresentation(
              district.overall_risk_level,
            );
            return (
              <li key={district.district_id}>
                <button
                  type="button"
                  onClick={() => onOpen(district.district_id)}
                  className="group flex w-full items-center gap-3.5 border-b border-[var(--color-border)] px-5 py-3 text-left transition-colors duration-[var(--duration-instant)] last:border-b-0 hover:bg-[var(--color-raised)]"
                >
                  <span className="w-7 shrink-0 font-mono text-[0.6875rem] tabular text-[var(--color-muted)]">
                    {(currentPage - 1) * DISTRICTS_PER_PAGE + index + 1}
                  </span>
                  <span
                    aria-hidden
                    className="h-8 w-1 shrink-0 rounded-full"
                    style={{
                      backgroundColor:
                        RISK_CSS_VARIABLE[district.overall_risk_level],
                    }}
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-h3">
                      {district.name}
                    </span>
                    <span className="block truncate text-[0.75rem] text-[var(--color-muted)]">
                      {district.region}
                      {district.leading_condition
                        ? ` · ${conditionLabel(district.leading_condition)}`
                        : ""}
                    </span>
                  </span>
                  <Icon
                    aria-hidden
                    strokeWidth={2}
                    className={cn("size-4 shrink-0", foreground)}
                  />
                  <RiskBadge
                    level={district.overall_risk_level}
                    size="sm"
                    showIcon={false}
                  />
                  <ArrowUpRight
                    aria-hidden
                    strokeWidth={2}
                    className="size-3.5 shrink-0 text-[var(--color-muted)] opacity-0 transition-opacity duration-[var(--duration-instant)] group-hover:opacity-100"
                  />
                </button>
              </li>
            );
          })}
        </ul>
      )}

      <Pagination
        page={currentPage}
        pageCount={pageCount}
        total={filtered.length}
        itemLabel="districts"
        onChange={setPage}
      />
    </>
  );
}

function AlertStream({
  alerts,
  loading,
  onOpen,
}: {
  alerts: Alert[] | undefined;
  loading: boolean;
  onOpen: (districtId: string) => void;
}) {
  return (
    <Card>
      <CardHeader
        title="Active alerts"
        description="Raised by the engine at high risk and above."
        action={
          <span className="flex items-center gap-1.5 text-small text-[var(--color-muted)]">
            <BellRing aria-hidden strokeWidth={2} className="size-3.5" />
            {alerts?.length ?? 0}
          </span>
        }
      />
      {loading ? (
        <CardBody className="space-y-2">
          {Array.from({ length: 3 }, (_, index) => (
            <Skeleton key={index} className="h-10 w-full" />
          ))}
        </CardBody>
      ) : !alerts || alerts.length === 0 ? (
        <CardBody>
          <p className="text-small text-[var(--color-muted)]">
            No district has crossed the alerting threshold. Alerts appear here
            the moment one does.
          </p>
        </CardBody>
      ) : (
        <ul className="max-h-[300px] overflow-y-auto">
          {alerts.slice(0, 8).map((alert) => (
            <li key={alert.alert_id}>
              <button
                type="button"
                onClick={() => onOpen(alert.district_id)}
                className="flex w-full items-center gap-3 border-b border-[var(--color-border)] px-5 py-2.5 text-left transition-colors duration-[var(--duration-instant)] last:border-b-0 hover:bg-[var(--color-raised)]"
              >
                <span
                  aria-hidden
                  className="size-1.5 shrink-0 rounded-full"
                  style={{ backgroundColor: RISK_CSS_VARIABLE[alert.level] }}
                />
                <span className="min-w-0 flex-1 truncate text-small">
                  <span className="font-medium">
                    {conditionLabel(alert.condition)}
                  </span>
                  <span className="text-[var(--color-muted)]">
                    {" "}
                    in {alert.district_name}
                  </span>
                </span>
                <span
                  className={cn(
                    "shrink-0 font-mono text-[0.75rem] tabular",
                    riskPresentation(alert.level).foreground,
                  )}
                >
                  {formatScore(alert.score)}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

const SPREAD_LIMIT = 8;

function ConditionSpread({
  alerts,
  loading,
}: {
  alerts: Alert[] | undefined;
  loading: boolean;
}) {
  const counts = useMemo(() => {
    const tally = new Map<
      string,
      { districts: Set<string>; level: RiskLevel }
    >();
    for (const alert of alerts ?? []) {
      const entry = tally.get(alert.condition) ?? {
        districts: new Set<string>(),
        level: alert.level,
      };
      entry.districts.add(alert.district_id);
      if (RISK_LEVEL_RANK[alert.level] > RISK_LEVEL_RANK[entry.level]) {
        entry.level = alert.level;
      }
      tally.set(alert.condition, entry);
    }
    return [...tally.entries()]
      .map(([condition, entry]) => ({
        condition,
        districts: entry.districts.size,
        level: entry.level,
      }))
      .sort((first, second) => second.districts - first.districts)
      .slice(0, SPREAD_LIMIT);
  }, [alerts]);

  const widest = counts[0]?.districts ?? 1;

  return (
    <Card>
      <CardHeader
        title="Conditions in play"
        description="Districts where each condition is at high risk or above."
      />
      {loading ? (
        <CardBody className="space-y-2">
          {Array.from({ length: 5 }, (_, index) => (
            <Skeleton key={index} className="h-6 w-full" />
          ))}
        </CardBody>
      ) : counts.length === 0 ? (
        <CardBody>
          <p className="text-small text-[var(--color-muted)]">
            No condition has crossed the alerting threshold anywhere.
          </p>
        </CardBody>
      ) : (
        <CardBody className="space-y-2.5">
          {counts.map(({ condition, districts, level }) => (
            <div key={condition} className="flex items-center gap-3">
              <span className="w-40 shrink-0 truncate text-small">
                {conditionLabel(condition)}
              </span>
              <span className="h-1.5 flex-1 rounded-[var(--radius-sm)] bg-[var(--color-border)]">
                <span
                  className="block h-full rounded-[var(--radius-sm)] transition-all duration-[var(--duration-medium)]"
                  style={{
                    width: `${(districts / widest) * 100}%`,
                    backgroundColor: RISK_CSS_VARIABLE[level],
                  }}
                />
              </span>
              <span className="w-16 shrink-0 text-right font-mono text-[0.75rem] tabular text-[var(--color-muted)]">
                {districts}
              </span>
            </div>
          ))}
        </CardBody>
      )}
    </Card>
  );
}
