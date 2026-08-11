"use client";

import { useQuery } from "@tanstack/react-query";
import {
  ArrowUpRight,
  ClipboardText,
  Clock,
  ShieldCheck,
  Users,
  type Icon as LucideIcon,
} from "@phosphor-icons/react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { RequireSession } from "@/components/shell/require-session";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import type { Alert } from "@/lib/api/types";
import { conditionLabel } from "@/lib/api/types";
import { useAuthenticatedSession } from "@/lib/auth/session";
import { cn } from "@/lib/cn";
import {
  RISK_CSS_VARIABLE,
  SCORE_EXPLANATION,
  formatScore,
  lagWindowText,
  onsetUrgency,
  riskPresentation,
} from "@/lib/risk";

export default function AlertsPage() {
  return (
    <RequireSession>
      <AlertsConsole />
    </RequireSession>
  );
}

function AlertsConsole() {
  const { token } = useAuthenticatedSession();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const alerts = useQuery({
    queryKey: ["alerts"],
    queryFn: () => api.alerts(token),
  });

  const list = alerts.data ?? [];
  const selected =
    list.find((alert) => alert.alert_id === selectedId) ?? list[0] ?? null;

  const soonest = [...list].sort(
    (first, second) =>
      onsetUrgency(first.lag_window) - onsetUrgency(second.lag_window),
  )[0];

  return (
    <div className="mx-auto max-w-[1600px] px-6 py-6">
      <header className="border-b border-[var(--color-border)] pb-6">
        <p className="text-eyebrow text-[var(--color-muted)]">Alerts</p>
        {alerts.isPending ? (
          <Skeleton className="mt-2 h-10 w-96" />
        ) : (
          <>
            <h1 className="mt-2 max-w-3xl text-display">
              {list.length === 0 ? (
                "No district has crossed the alerting threshold"
              ) : (
                <>
                  <span
                    style={{
                      color: RISK_CSS_VARIABLE[list[0]?.level ?? "high"],
                    }}
                  >
                    {list.length} active{" "}
                    {list.length === 1 ? "alert" : "alerts"}
                  </span>{" "}
                  need a decision
                </>
              )}
            </h1>
            {soonest ? (
              <p className="mt-2.5 text-small text-[var(--color-muted)]">
                Soonest onset:{" "}
                <span className="text-[var(--color-ink)]">
                  {conditionLabel(soonest.condition)} in {soonest.district_name}
                </span>
                , cases expected in {lagWindowText(soonest.lag_window)}
              </p>
            ) : null}
          </>
        )}
      </header>

      {alerts.isPending ? (
        <div className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,3fr)_minmax(0,4fr)]">
          <Skeleton className="h-[420px]" />
          <Skeleton className="h-[420px]" />
        </div>
      ) : list.length === 0 ? (
        <Card className="mt-6">
          <CardBody className="flex items-start gap-3 py-8">
            <ShieldCheck
              aria-hidden
              className="mt-0.5 size-5 shrink-0 text-[var(--color-risk-low)]"
            />
            <div>
              <p className="text-h3">Nothing is escalating right now</p>
              <p className="mt-1 max-w-xl text-small text-[var(--color-muted)]">
                An alert is raised the moment a district crosses high risk. The
                engine re-evaluates every district against live climate on each
                request, so this list is current, not cached.
              </p>
            </div>
          </CardBody>
        </Card>
      ) : (
        <div className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,3fr)_minmax(0,4fr)]">
          <Card className="overflow-hidden">
            <CardHeader
              title="Triage queue"
              description="Ranked by score. Highest first."
            />
            <ul className="max-h-[640px] overflow-y-auto">
              {list.map((alert) => (
                <AlertRow
                  key={alert.alert_id}
                  alert={alert}
                  selected={selected?.alert_id === alert.alert_id}
                  onSelect={() => setSelectedId(alert.alert_id)}
                />
              ))}
            </ul>
          </Card>

          {selected ? <AlertDetail alert={selected} /> : null}
        </div>
      )}
    </div>
  );
}

function AlertRow({
  alert,
  selected,
  onSelect,
}: {
  alert: Alert;
  selected: boolean;
  onSelect: () => void;
}) {
  const { icon: Icon, foreground } = riskPresentation(alert.level);

  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        aria-current={selected ? "true" : undefined}
        className={cn(
          "flex w-full items-center gap-3.5 border-b border-[var(--color-border)] px-5 py-3 text-left",
          "transition-colors duration-[var(--duration-instant)] last:border-b-0",
          selected
            ? "bg-[var(--color-raised)]"
            : "hover:bg-[var(--color-raised)]",
        )}
      >
        <span
          aria-hidden
          className="h-9 w-1 shrink-0 rounded-full"
          style={{ backgroundColor: RISK_CSS_VARIABLE[alert.level] }}
        />
        <Icon aria-hidden className={cn("size-4 shrink-0", foreground)} />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-h3">
            {conditionLabel(alert.condition)}
          </span>
          <span className="block truncate text-[0.75rem] text-[var(--color-muted)]">
            {alert.district_name} · {alert.region} · cases in{" "}
            {lagWindowText(alert.lag_window)}
          </span>
        </span>
        <span
          className={cn("shrink-0 font-mono text-small tabular", foreground)}
        >
          {formatScore(alert.score)}
        </span>
      </button>
    </li>
  );
}

function AlertDetail({ alert }: { alert: Alert }) {
  const router = useRouter();
  const { icon: Icon, foreground } = riskPresentation(alert.level);

  return (
    <Card className="self-start">
      <CardHeader
        title={`${conditionLabel(alert.condition)} — ${alert.district_name}`}
        description={`Raised ${alert.raised_on} · ${alert.region}`}
        action={<RiskBadge level={alert.level} />}
      />
      <CardBody className="space-y-5">
        <div className="grid grid-cols-3 gap-4">
          <Metric
            icon={Icon}
            label="Risk score / 100"
            value={formatScore(alert.score)}
            tone={foreground}
            hint={SCORE_EXPLANATION}
          />
          <Metric
            icon={Clock}
            label="Onset window"
            value={lagWindowText(alert.lag_window)}
          />
          <Metric
            icon={Users}
            label="Most at risk"
            value={alert.vulnerable_group}
            small
          />
        </div>

        <div>
          <p className="text-micro text-[var(--color-muted)]">
            Conditions that triggered this
          </p>
          <ul className="mt-2.5 space-y-2">
            {alert.reasons.map((reason) => (
              <li key={reason} className="flex gap-2.5 text-small">
                <span
                  aria-hidden
                  className="mt-1.5 size-1.5 shrink-0 rounded-full"
                  style={{ backgroundColor: RISK_CSS_VARIABLE[alert.level] }}
                />
                {reason}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-[var(--radius-md)] border border-[var(--color-accent)]/25 bg-[var(--color-accent-subtle)] px-3.5 py-3">
          <p className="flex items-center gap-1.5 text-micro text-[var(--color-accent)]">
            <ClipboardText aria-hidden className="size-3.5" />
            Recommended action
          </p>
          <p className="mt-1.5 text-small">{alert.recommended_action}</p>
        </div>

        <button
          type="button"
          onClick={() => router.push(`/districts/${alert.district_id}`)}
          className="flex items-center gap-1.5 text-small text-[var(--color-accent)] transition-opacity duration-[var(--duration-instant)] hover:opacity-80"
        >
          Open {alert.district_name}
          <ArrowUpRight aria-hidden className="size-3.5" />
        </button>
      </CardBody>
    </Card>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  tone,
  small = false,
  hint,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  tone?: string;
  small?: boolean;
  hint?: string;
}) {
  return (
    <div title={hint}>
      <p className="flex items-center gap-1.5 text-[0.6875rem] text-[var(--color-muted)]">
        <Icon aria-hidden className="size-3" />
        {label}
      </p>
      <p
        className={cn(
          "mt-1 font-medium tabular",
          small ? "text-[0.8125rem] leading-snug" : "text-h2",
          tone,
        )}
      >
        {value}
      </p>
    </div>
  );
}
