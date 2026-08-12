"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowUpRight,
  CaretDown,
  MapPinLine,
  Plus,
  SealCheck,
  Tray,
  User,
  X,
} from "@phosphor-icons/react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent, type ReactNode } from "react";

import { DistrictSwitcher } from "@/components/district/district-switcher";
import { RequireSession } from "@/components/shell/require-session";
import { ReportProgressPanel } from "@/components/reports/report-progress";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import type {
  UserResponse,
  CommunityReport,
  ReportType,
  VerificationStatus,
} from "@/lib/api/types";
import { useAuthenticatedSession } from "@/lib/auth/session";
import { cn } from "@/lib/cn";
import {
  REPORT_TYPES,
  formatCoordinates,
  reportPresentation,
} from "@/lib/reports";
import { relativeDay } from "@/lib/risk";

export default function ReportsPage() {
  return (
    <RequireSession>
      <FieldReports />
    </RequireSession>
  );
}

function FieldReports() {
  const { token, user } = useAuthenticatedSession();
  const router = useRouter();
  const scopedDistrictId =
    user?.scope.level === "district" ? user.scope.district_id : null;

  const [districtFilter, setDistrictFilter] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<ReportType | null>(null);
  const [composing, setComposing] = useState(false);
  const [opened, setOpened] = useState<string | null>(null);

  const districtId = scopedDistrictId ?? districtFilter;

  const reports = useQuery({
    queryKey: ["reports", districtId ?? "all", typeFilter ?? "all"],
    queryFn: () =>
      api.reports(token, districtId ?? undefined, typeFilter ?? undefined),
  });

  const districts = useQuery({
    queryKey: ["districts"],
    queryFn: () => api.districts(token),
  });

  const districtNames = new Map(
    (districts.data ?? []).map((district) => [
      district.district_id,
      district.name,
    ]),
  );

  const list = reports.data ?? [];
  const pending = list.filter((r) => r.verification === "pending").length;

  return (
    <div className="mx-auto max-w-[1400px] px-6 py-6">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--color-border)] pb-6">
        <div>
          <p className="text-eyebrow text-[var(--color-muted)]">
            Field reports
          </p>
          <h1 className="mt-2 text-h1">
            {reports.isPending
              ? "Loading reports"
              : `${list.length} ${list.length === 1 ? "report" : "reports"} from the community`}
          </h1>
          <p className="mt-1 text-small text-[var(--color-muted)]">
            Only verified reports reach the engine.{" "}
            {pending > 0
              ? `${pending} awaiting verification.`
              : "Nothing is awaiting verification."}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {scopedDistrictId === null ? (
            <DistrictSwitcher
              token={token}
              value={districtId}
              onChange={setDistrictFilter}
              className="w-56"
            />
          ) : null}
          <Button
            variant="primary"
            size="md"
            onClick={() => setComposing(true)}
          >
            <Plus aria-hidden className="size-4" />
            Log a report
          </Button>
        </div>
      </header>

      <div className="mt-5 flex flex-wrap gap-1.5">
        <FilterChip
          active={typeFilter === null}
          onClick={() => setTypeFilter(null)}
          label="All types"
        />
        {REPORT_TYPES.map((type) => {
          const { label, icon: Icon } = reportPresentation(type);
          return (
            <FilterChip
              key={type}
              active={typeFilter === type}
              onClick={() => setTypeFilter(typeFilter === type ? null : type)}
              label={label}
              icon={<Icon aria-hidden className="size-3.5" />}
            />
          );
        })}
      </div>

      {composing ? (
        <ComposeReport
          token={token}
          districtId={districtId}
          onClose={() => setComposing(false)}
        />
      ) : null}

      <Card className="mt-5">
        <CardHeader title="Reported hazards" description="Most recent first." />
        {reports.isPending ? (
          <CardBody className="space-y-2">
            {Array.from({ length: 4 }, (_, index) => (
              <Skeleton key={index} className="h-16 w-full" />
            ))}
          </CardBody>
        ) : reports.isError ? (
          <CardBody>
            <p className="text-small text-[var(--color-muted)]">
              {reports.error.message}
            </p>
          </CardBody>
        ) : list.length === 0 ? (
          <CardBody className="flex items-start gap-3 py-8">
            <Tray
              aria-hidden
              className="mt-0.5 size-5 shrink-0 text-[var(--color-muted)]"
            />
            <div>
              <p className="text-h3">No reports match this filter</p>
              <p className="mt-1 max-w-lg text-small text-[var(--color-muted)]">
                Reports submitted from the Dawuro app or logged here appear
                immediately, and feed the readiness count for their district.
              </p>
            </div>
          </CardBody>
        ) : (
          <ul>
            {[...list]
              .sort((first, second) =>
                second.submitted_on.localeCompare(first.submitted_on),
              )
              .map((report) => (
                <ReportRow
                  key={report.report_id}
                  report={report}
                  districtName={
                    districtNames.get(report.district_id) ?? report.district_id
                  }
                  token={token ?? ""}
                  user={user ?? null}
                  expanded={opened === report.report_id}
                  onToggle={() =>
                    setOpened(
                      opened === report.report_id ? null : report.report_id,
                    )
                  }
                  onOpenDistrict={() =>
                    router.push(`/districts/${report.district_id}`)
                  }
                />
              ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function FilterChip({
  active,
  onClick,
  label,
  icon,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  icon?: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs",
        "transition-colors duration-[var(--duration-instant)]",
        active
          ? "border-[var(--color-accent)]/40 bg-[var(--color-accent-subtle)] font-medium text-[var(--color-accent)]"
          : "border-[var(--color-border)] text-[var(--color-muted)] hover:border-[var(--color-border-strong)] hover:text-[var(--color-ink)]",
      )}
    >
      {icon}
      {label}
    </button>
  );
}

const VERIFICATION_TONE: Record<VerificationStatus, string> = {
  pending: "text-[var(--color-muted)] border-[var(--color-border)]",
  verified: "text-[var(--color-risk-low)] border-[var(--color-risk-low)]/40",
  rejected:
    "text-[var(--color-risk-severe)] border-[var(--color-risk-severe)]/40",
};

const VERIFICATION_LABEL: Record<VerificationStatus, string> = {
  pending: "Awaiting verification",
  verified: "Verified — feeding the engine",
  rejected: "Rejected",
};

function ReportRow({
  report,
  districtName,
  token,
  user,
  expanded,
  onToggle,
  onOpenDistrict,
}: {
  report: CommunityReport;
  districtName: string;
  token: string;
  user: UserResponse | null;
  expanded: boolean;
  onToggle: () => void;
  onOpenDistrict: () => void;
}) {
  const { label, icon: Icon } = reportPresentation(report.report_type);
  const coordinates = formatCoordinates(report.latitude, report.longitude);

  const row = (
    <div className="flex items-start gap-3.5 px-5 py-3.5">
      <span
        aria-hidden
        className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-raised)]"
      >
        <Icon className="size-4 text-[var(--color-muted)]" />
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-x-2">
          <span className="text-h3">{label}</span>
          <span className="text-[0.75rem] text-[var(--color-muted)]">
            {relativeDay(report.submitted_on)}
          </span>
        </div>
        <p className="mt-0.5 text-small">{report.note}</p>
        <p className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[0.6875rem] text-[var(--color-muted)]">
          <span
            className={cn(
              "flex items-center gap-1 rounded-[var(--radius-sm)] border px-1.5 py-0.5",
              VERIFICATION_TONE[report.verification],
            )}
          >
            <SealCheck aria-hidden className="size-3" />
            {VERIFICATION_LABEL[report.verification]}
            {report.verified_by ? ` by ${report.verified_by}` : ""}
          </span>
          <span className="flex items-center gap-1">
            <User aria-hidden className="size-3" />
            {report.submitted_by}
          </span>
          {coordinates ? (
            <span className="flex items-center gap-1 font-mono">
              <MapPinLine aria-hidden className="size-3" />
              {coordinates}
            </span>
          ) : null}
        </p>
      </div>

      <div className="flex shrink-0 flex-col items-end gap-1.5">
        <button
          type="button"
          onClick={onOpenDistrict}
          className="flex items-center gap-1 text-[0.75rem] text-[var(--color-muted)] transition-colors duration-[var(--duration-instant)] hover:text-[var(--color-accent)]"
        >
          {districtName}
          <ArrowUpRight aria-hidden className="size-3" />
        </button>
        <Button
          size="sm"
          variant="ghost"
          onClick={onToggle}
          aria-expanded={expanded}
        >
          {expanded ? "Hide progress" : "Progress"}
          <CaretDown
            aria-hidden
            className={cn(
              "size-3.5 transition-transform duration-[var(--duration-short)]",
              expanded && "rotate-180",
            )}
          />
        </Button>
      </div>
    </div>
  );

  return (
    <li className="border-b border-[var(--color-border)] last:border-b-0">
      {row}
      {expanded ? (
        <div className="px-5 pb-4">
          {report.photo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={report.photo_url}
              alt={`Photograph submitted with the ${label.toLowerCase()} report`}
              className="mb-3 max-h-64 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] object-cover"
            />
          ) : null}
          <ReportProgressPanel
            reportId={report.report_id}
            token={token}
            user={user}
          />
        </div>
      ) : null}
    </li>
  );
}

function ComposeReport({
  token,
  districtId,
  onClose,
}: {
  token: string;
  districtId: string | null;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [type, setType] = useState<ReportType>("stagnant_water");
  const [note, setNote] = useState("");

  const submit = useMutation({
    mutationFn: () =>
      api.submitReport(token, {
        district_id: districtId as string,
        report_type: type,
        note,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["reports"] });
      onClose();
    },
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    submit.mutate();
  }

  return (
    <Card className="mt-5">
      <CardHeader
        title="Log a field report"
        description={
          districtId
            ? "Recorded against your account and visible immediately."
            : "Choose a district above before logging a report."
        }
        action={
          <Button
            variant="ghost"
            size="icon"
            aria-label="Close"
            onClick={onClose}
          >
            <X aria-hidden className="size-4" />
          </Button>
        }
      />
      <CardBody>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <p className="text-small font-medium">What did you observe?</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {REPORT_TYPES.map((option) => {
                const { label, icon: Icon, hint } = reportPresentation(option);
                return (
                  <button
                    key={option}
                    type="button"
                    title={hint}
                    onClick={() => setType(option)}
                    aria-pressed={type === option}
                    className={cn(
                      "flex items-center gap-1.5 rounded-[var(--radius-md)] border px-2.5 py-1.5 text-xs",
                      "transition-colors duration-[var(--duration-instant)]",
                      type === option
                        ? "border-[var(--color-accent)]/40 bg-[var(--color-accent-subtle)] font-medium text-[var(--color-accent)]"
                        : "border-[var(--color-border)] text-[var(--color-muted)] hover:border-[var(--color-border-strong)]",
                    )}
                  >
                    <Icon aria-hidden className="size-3.5" />
                    {label}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label
              htmlFor="report-note"
              className="block text-small font-medium"
            >
              What exactly did you see?
            </label>
            <textarea
              id="report-note"
              value={note}
              onChange={(event) => setNote(event.target.value)}
              rows={3}
              maxLength={1000}
              placeholder="Water has been standing behind the market for about a week"
              className="mt-1.5 w-full resize-y rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-small text-[var(--color-ink)] transition-colors duration-[var(--duration-instant)] placeholder:text-[var(--color-muted)] hover:border-[var(--color-border-strong)]"
            />
          </div>

          {submit.isError ? (
            <p
              role="alert"
              className="text-[0.75rem] text-[var(--color-risk-severe)]"
            >
              {submit.error.message}
            </p>
          ) : null}

          <div className="flex items-center gap-2">
            <Button
              type="submit"
              variant="primary"
              disabled={
                submit.isPending || note.trim() === "" || districtId === null
              }
            >
              Submit report
            </Button>
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
