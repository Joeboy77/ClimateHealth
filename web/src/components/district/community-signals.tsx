"use client";

import { MessageSquareWarning } from "lucide-react";

import { Card, CardBody, CardHeader } from "@/components/ui/card";
import type { CommunitySignal } from "@/lib/api/types";

/**
 * Proposal section 6.2: in a thinly instrumented district a verified citizen
 * report is often the highest-resolution signal available. This panel shows
 * exactly which engine inputs came from residents rather than instruments.
 */
export function CommunitySignalsPanel({
  signals,
}: {
  signals: readonly CommunitySignal[];
}) {
  return (
    <Card>
      <CardHeader
        title="Signals from residents"
        description="Verified reports the engine used as evidence."
      />
      {signals.length === 0 ? (
        <CardBody>
          <p className="text-small text-[var(--color-muted)]">
            No verified reports are contributing here. A report only becomes a
            signal once a coordinator confirms it, so unverified submissions never
            move a risk score.
          </p>
        </CardBody>
      ) : (
        <CardBody className="space-y-3">
          {signals.map((signal) => (
            <div key={signal.signal} className="flex items-center gap-3">
              <MessageSquareWarning
                aria-hidden
                strokeWidth={2}
                className="size-4 shrink-0 text-[var(--color-accent)]"
              />
              <span className="min-w-0 flex-1">
                <span className="block text-small font-medium">{signal.label}</span>
                <span className="block text-[0.6875rem] text-[var(--color-muted)]">
                  {signal.report_count} verified{" "}
                  {signal.report_count === 1 ? "report" : "reports"} · newest{" "}
                  {signal.newest_report_on}
                </span>
              </span>
              <span className="shrink-0 font-mono text-small tabular text-[var(--color-accent)]">
                {signal.value.toFixed(2)}
              </span>
            </div>
          ))}
          <p className="border-t border-[var(--color-border)] pt-2.5 text-[0.6875rem] text-[var(--color-muted)]">
            Community evidence is capped below certainty and only fills signals no
            instrument reports. A measured value is never overwritten.
          </p>
        </CardBody>
      )}
    </Card>
  );
}
