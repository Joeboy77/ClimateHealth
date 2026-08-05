import { api, uploadReportPhoto } from "@/lib/api/client";
import type { ReportType } from "@/lib/api/types";
import { persistent } from "./store";

const QUEUE_KEY = "dawuro.report-queue";
/** Enough attempts to ride out a bad afternoon, not so many that a doomed report loops. */
const MAXIMUM_ATTEMPTS = 8;

export type QueuedReport = {
  readonly id: string;
  readonly districtId: string;
  readonly reportType: ReportType;
  readonly note: string;
  readonly photoUri: string | null;
  readonly latitude: number | null;
  readonly longitude: number | null;
  readonly queuedAt: string;
  readonly attempts: number;
};

export type FlushResult = {
  readonly sent: number;
  readonly remaining: number;
};

/**
 * Reports written without a connection.
 *
 * The people most exposed to climate risk have the least reliable connectivity, so a
 * report that cannot be sent is held rather than lost, and the person is told it is held.
 * Photographs are kept by their local file URI: copying the bytes into storage would
 * double the space used for something the phone already has.
 */

function read(): QueuedReport[] {
  const raw = persistent().getString(QUEUE_KEY);
  if (raw === undefined) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? (parsed as QueuedReport[]) : [];
  } catch {
    // A queue we cannot parse is a queue we cannot send. Start clean rather than
    // failing on every launch.
    return [];
  }
}

function write(reports: readonly QueuedReport[]): void {
  persistent().set(QUEUE_KEY, JSON.stringify(reports));
}

export function queued(): QueuedReport[] {
  return read();
}

export function queuedCount(): number {
  return read().length;
}

export function enqueue(
  report: Omit<QueuedReport, "id" | "queuedAt" | "attempts">,
): QueuedReport {
  const entry: QueuedReport = {
    ...report,
    id: `queued-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    queuedAt: new Date().toISOString(),
    attempts: 0,
  };
  write([...read(), entry]);
  return entry;
}

export function discard(id: string): void {
  write(read().filter((entry) => entry.id !== id));
}

/**
 * Try to send everything held. Anything that fails stays, with its attempt count raised;
 * anything that has failed too often is dropped, because a report nobody can send is
 * only taking up room and will never be verified.
 */
export async function flush(token: string): Promise<FlushResult> {
  const pending = read();
  if (pending.length === 0) return { sent: 0, remaining: 0 };

  const keep: QueuedReport[] = [];
  let sent = 0;

  for (const entry of pending) {
    try {
      const photoReference =
        entry.photoUri === null ? null : await uploadReportPhoto(token, entry.photoUri);

      await api.submitReport(token, {
        district_id: entry.districtId,
        report_type: entry.reportType,
        note: entry.note,
        photo_reference: photoReference,
        latitude: entry.latitude,
        longitude: entry.longitude,
      });
      sent += 1;
    } catch {
      const attempts = entry.attempts + 1;
      if (attempts < MAXIMUM_ATTEMPTS) keep.push({ ...entry, attempts });
    }
  }

  write(keep);
  return { sent, remaining: keep.length };
}
