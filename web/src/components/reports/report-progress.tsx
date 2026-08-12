"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle, Prohibit, Wrench } from "@phosphor-icons/react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import type { ReportProgress, UserResponse } from "@/lib/api/types";
import { cn } from "@/lib/cn";

const ORDERED_STAGES = [
  { stage: "submitted", label: "Submitted" },
  { stage: "validated", label: "Validated" },
  { stage: "in_progress", label: "In progress" },
  { stage: "resolved", label: "Resolved" },
] as const;

const STAGE_ACTIONS: Record<
  string,
  { label: string; icon: typeof CheckCircle; needsNote: boolean }
> = {
  validated: {
    label: "Validate on the ground",
    icon: CheckCircle,
    needsNote: true,
  },
  rejected: { label: "Could not confirm", icon: Prohibit, needsNote: true },
  in_progress: { label: "Start work", icon: Wrench, needsNote: false },
  resolved: { label: "Mark resolved", icon: CheckCircle, needsNote: true },
};

/** Only the Ɔhwɛfoɔ judges authenticity; only an agency reports on the work. */
function permitted(stage: string, user: UserResponse | null): boolean {
  if (user === null) return false;
  if (stage === "validated" || stage === "rejected")
    return user.can_validate_reports;
  return user.can_assign_actions || user.role === "responder";
}

/**
 * A report's progress, and every hand it has passed through.
 *
 * The bar is the fast answer and the timeline is the accountable one: who went, when,
 * and what they wrote when they got there. A status that cannot say who set it is the
 * thing agencies already distrust about paper reporting.
 */
export function ReportProgressPanel({
  reportId,
  token,
  user,
}: {
  reportId: string;
  token: string;
  user: UserResponse | null;
}) {
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");

  const progress = useQuery({
    queryKey: ["report-progress", reportId],
    queryFn: () => api.reportProgress(token, reportId),
  });

  const advance = useMutation({
    mutationFn: (stage: string) =>
      api.advanceReportStage(token, reportId, stage, note.trim() || null),
    onSuccess: (updated) => {
      queryClient.setQueryData<ReportProgress>(
        ["report-progress", reportId],
        updated,
      );
      void queryClient.invalidateQueries({ queryKey: ["reports"] });
      setNote("");
    },
  });

  if (progress.isPending) return <Skeleton className="h-28 w-full" />;
  if (!progress.data) return null;

  const { stage, stage_label, percent, next_stages, timeline } = progress.data;
  const rejected = stage === "rejected";
  const reachedIndex = ORDERED_STAGES.findIndex(
    (entry) => entry.stage === stage,
  );

  const barColour = rejected
    ? "var(--color-muted)"
    : stage === "resolved"
      ? "var(--color-risk-low)"
      : "var(--color-accent)";

  const available = next_stages.filter((next) => permitted(next, user));

  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-raised)] p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="text-eyebrow" style={{ color: barColour }}>
          {stage_label}
        </span>
        <span className="text-small tabular text-[var(--color-muted)]">
          {percent}%
        </span>
      </div>

      <div
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Report progress: ${stage_label}`}
        className="mt-2 h-2 w-full overflow-hidden rounded-full bg-[var(--color-border)]"
      >
        <div
          className="h-full rounded-full transition-[width] duration-[var(--duration-risk)] ease-[var(--ease-out)]"
          style={{ width: `${percent}%`, backgroundColor: barColour }}
        />
      </div>

      {rejected ? null : (
        <ol className="mt-2 flex justify-between">
          {ORDERED_STAGES.map((entry, index) => (
            <li
              key={entry.stage}
              className={cn(
                "text-[0.6875rem]",
                index <= reachedIndex
                  ? "text-[var(--color-ink)]"
                  : "text-[var(--color-muted)]",
              )}
            >
              {entry.label}
            </li>
          ))}
        </ol>
      )}

      {timeline.length > 0 ? (
        <ul className="mt-4 space-y-2 border-t border-[var(--color-border)] pt-3">
          {timeline.map((entry, index) => (
            <li key={`${entry.stage}-${index}`} className="text-[0.75rem]">
              <span className="text-[var(--color-ink)]">
                {entry.stage_label}
              </span>{" "}
              <span className="text-[var(--color-muted)]">
                by {entry.actor_name}, {entry.actor_role}
              </span>
              {entry.note ? (
                <p className="mt-0.5 text-[var(--color-muted)]">
                  &ldquo;{entry.note}&rdquo;
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}

      {available.length > 0 ? (
        <div className="mt-4 border-t border-[var(--color-border)] pt-3">
          <label htmlFor={`note-${reportId}`} className="sr-only">
            What you found or did
          </label>
          <input
            id={`note-${reportId}`}
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="What you found, or what was done"
            className="h-8 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 text-small text-[var(--color-ink)] placeholder:text-[var(--color-muted)]"
          />
          <div className="mt-2 flex flex-wrap gap-1.5">
            {available.map((next) => {
              const action = STAGE_ACTIONS[next];
              if (action === undefined) return null;
              const Icon = action.icon;
              return (
                <Button
                  key={next}
                  size="sm"
                  variant={next === "rejected" ? "ghost" : "primary"}
                  disabled={advance.isPending}
                  onClick={() => advance.mutate(next)}
                >
                  <Icon aria-hidden className="size-3.5" />
                  {action.label}
                </Button>
              );
            })}
          </div>
          {advance.isError ? (
            <p
              role="alert"
              className="mt-2 text-[0.75rem] text-[var(--color-risk-severe)]"
            >
              {advance.error.message}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
