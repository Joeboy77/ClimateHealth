"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  ChatTeardrop,
  DeviceMobile,
  PaperPlaneTilt,
  SealCheck,
  ShieldWarning,
  Warning,
} from "@phosphor-icons/react";
import { useMemo, useState } from "react";

import { RequireSession } from "@/components/shell/require-session";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import type { SmsPreview, UssdReply } from "@/lib/api/types";
import { useAuthenticatedSession } from "@/lib/auth/session";
import { cn } from "@/lib/cn";

const LANGUAGES: ReadonlyArray<{ code: string; label: string }> = [
  { code: "en", label: "English" },
  { code: "tw", label: "Twi" },
];

const GSM7_SEGMENT = 160;
const UCS2_SEGMENT = 70;

export default function OutreachPage() {
  return (
    <RequireSession>
      <OutreachConsole />
    </RequireSession>
  );
}

function OutreachConsole() {
  const { token, user } = useAuthenticatedSession();
  const [language, setLanguage] = useState("en");

  const scopedDistrictId =
    user?.scope.level === "district" ? user.scope.district_id : null;

  const districts = useQuery({
    queryKey: ["districts"],
    queryFn: () => api.districts(token),
  });

  const [selected, setSelected] = useState<string | null>(scopedDistrictId);
  const districtId =
    selected ?? scopedDistrictId ?? districts.data?.[0]?.district_id ?? null;

  const preview = useQuery({
    queryKey: ["sms-preview", districtId, language],
    queryFn: () => api.smsPreview(token, districtId ?? "", language),
    enabled: districtId !== null,
  });

  return (
    <div className="mx-auto max-w-[1600px] px-6 py-6">
      <header className="border-b border-[var(--color-border)] pb-6">
        <p className="text-eyebrow text-[var(--color-muted)]">Outreach</p>
        <h1 className="mt-2 max-w-3xl text-display">
          The warning, on a phone that cannot open an app
        </h1>
        <p className="mt-2.5 max-w-2xl text-small text-[var(--color-muted)]">
          The same engine decision, delivered by SMS and by USSD shortcode. No
          smartphone, no data bundle, no literacy in English required.
        </p>
      </header>

      <div className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div className="space-y-5">
          <Card>
            <CardHeader
              title="Message preview"
              description="Exactly what arrives. Composed from the engine, never typed by hand."
              action={
                <div className="flex gap-1.5">
                  {LANGUAGES.map((entry) => (
                    <button
                      key={entry.code}
                      type="button"
                      onClick={() => setLanguage(entry.code)}
                      className={cn(
                        "rounded-[var(--radius-sm)] border px-2.5 py-1 text-[0.75rem]",
                        "transition-colors duration-[var(--duration-instant)]",
                        language === entry.code
                          ? "border-[var(--color-accent)] text-[var(--color-accent)]"
                          : "border-[var(--color-border)] text-[var(--color-muted)] hover:text-[var(--color-ink)]",
                      )}
                    >
                      {entry.label}
                    </button>
                  ))}
                </div>
              }
            />
            <CardBody className="space-y-4">
              {!scopedDistrictId && districts.data ? (
                <label className="block">
                  <span className="text-micro text-[var(--color-muted)]">
                    District
                  </span>
                  <select
                    value={districtId ?? ""}
                    onChange={(event) => setSelected(event.target.value)}
                    className="mt-1.5 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-raised)] px-3 py-2 text-small text-[var(--color-ink)]"
                  >
                    {districts.data.map((district) => (
                      <option
                        key={district.district_id}
                        value={district.district_id}
                      >
                        {district.name} — {district.region}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              {preview.isPending ? (
                <Skeleton className="h-32 w-full" />
              ) : preview.isError ? (
                <p className="text-small text-[var(--color-muted)]">
                  {preview.error.message}
                </p>
              ) : preview.data.has_alert && preview.data.alert ? (
                <MessagePreview preview={preview.data} />
              ) : (
                <p className="flex items-start gap-2.5 text-small text-[var(--color-muted)]">
                  <ShieldWarning
                    aria-hidden
                    className="mt-0.5 size-4 shrink-0"
                  />
                  Nothing in {preview.data.district_name} is above the warning
                  level, so there is no message to send. A broadcast is refused
                  rather than composed from a moderate risk.
                </p>
              )}
            </CardBody>
          </Card>

          {preview.data?.has_alert ? (
            <BroadcastCard
              token={token}
              districtId={districtId ?? ""}
              language={language}
              preview={preview.data}
              isCoordinator={user?.role === "coordinator"}
            />
          ) : null}
        </div>

        <UssdSimulator token={token} />
      </div>
    </div>
  );
}

function MessagePreview({ preview }: { preview: SmsPreview }) {
  const alert = preview.alert;
  if (!alert) return null;

  const limit = alert.encoding === "gsm7" ? GSM7_SEGMENT : UCS2_SEGMENT;
  const used = Math.min(alert.character_count / limit, 1);

  return (
    <div className="space-y-3.5">
      <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-raised)] p-4">
        <p className="flex items-center gap-2 text-[0.6875rem] text-[var(--color-muted)]">
          <ChatTeardrop aria-hidden className="size-3" />
          From {preview.sender_id}
        </p>
        <p className="mt-2 font-mono text-small leading-relaxed text-[var(--color-ink)]">
          {alert.body}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
        <span className="flex items-baseline gap-2">
          <span className="font-mono text-h2 tabular">
            {alert.character_count}
          </span>
          <span className="text-[0.75rem] text-[var(--color-muted)]">
            of {limit} characters
          </span>
        </span>
        <span
          className="text-[0.75rem] text-[var(--color-muted)]"
          title={
            alert.encoding === "gsm7"
              ? "Plain GSM-7 text: 160 characters per segment"
              : "A non-GSM character forces UCS-2: only 70 characters per segment"
          }
        >
          {alert.encoding === "gsm7" ? "GSM-7" : "UCS-2"} ·{" "}
          {alert.segments === 1
            ? "one segment"
            : `${alert.segments} segments, ${alert.segments}x the cost`}
        </span>
      </div>

      <div
        className="h-1 overflow-hidden rounded-full bg-[var(--color-border)]"
        role="presentation"
      >
        <div
          className="h-full rounded-full"
          style={{
            width: `${used * 100}%`,
            backgroundColor:
              alert.segments === 1
                ? "var(--color-risk-low)"
                : "var(--color-risk-high)",
          }}
        />
      </div>

      <SenderStatus preview={preview} />
    </div>
  );
}

function SenderStatus({ preview }: { preview: SmsPreview }) {
  const status = preview.sender_status;
  const approved = status.approval.toLowerCase() === "approved";
  const unchecked = status.approval === "Not checked";

  return (
    <p
      className="flex items-start gap-2 text-[0.75rem]"
      style={{
        color: approved
          ? "var(--color-risk-low)"
          : unchecked
            ? "var(--color-muted)"
            : "var(--color-risk-high)",
      }}
    >
      {approved ? (
        <SealCheck aria-hidden className="mt-0.5 size-3.5 shrink-0" />
      ) : (
        <Warning aria-hidden className="mt-0.5 size-3.5 shrink-0" />
      )}
      Sender ID {status.sender_id}: {status.approval}
      {approved
        ? ". Cleared to send on every network."
        : unchecked
          ? ". No provider key configured, so nothing can leave."
          : ". The network would reject a broadcast under this name."}
    </p>
  );
}

function BroadcastCard({
  token,
  districtId,
  language,
  preview,
  isCoordinator,
}: {
  token: string;
  districtId: string;
  language: string;
  preview: SmsPreview;
  isCoordinator: boolean;
}) {
  const [recipients, setRecipients] = useState("233241234567");

  const numbers = useMemo(
    () =>
      recipients
        .split(/[\s,]+/)
        .map((entry) => entry.trim())
        .filter(Boolean),
    [recipients],
  );

  const send = useMutation({
    mutationFn: () => api.sendSms(token, districtId, numbers, language),
  });

  const live = preview.delivery_mode === "live";

  return (
    <Card>
      <CardHeader
        title="Broadcast"
        description={
          live
            ? "Delivery is live. These messages will actually be sent."
            : "Delivery is set to preview. Nothing leaves the building."
        }
        action={
          <span
            className="rounded-[var(--radius-sm)] border px-2 py-0.5 text-[0.625rem] font-semibold uppercase tracking-wide"
            style={{
              borderColor: live
                ? "var(--color-risk-high)"
                : "var(--color-border)",
              color: live ? "var(--color-risk-high)" : "var(--color-muted)",
            }}
          >
            {preview.delivery_mode}
          </span>
        }
      />
      <CardBody className="space-y-3.5">
        <label className="block">
          <span className="text-micro text-[var(--color-muted)]">
            Recipients ({numbers.length})
          </span>
          <textarea
            value={recipients}
            onChange={(event) => setRecipients(event.target.value)}
            rows={2}
            className="mt-1.5 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-raised)] px-3 py-2 font-mono text-small text-[var(--color-ink)]"
          />
        </label>

        {isCoordinator ? (
          <Button
            onClick={() => send.mutate()}
            disabled={send.isPending || numbers.length === 0}
          >
            <PaperPlaneTilt aria-hidden className="size-3.5" />
            {live ? "Send now" : "Run through the sender"}
          </Button>
        ) : (
          <p className="text-small text-[var(--color-muted)]">
            Only a coordinator may broadcast to the public.
          </p>
        )}

        {send.isError ? (
          <p className="text-small text-[var(--color-risk-high)]">
            {send.error.message}
          </p>
        ) : null}

        {send.data ? (
          <ul className="space-y-1.5">
            {send.data.deliveries.map((delivery) => (
              <li
                key={delivery.reference}
                className="flex items-baseline justify-between gap-3 text-[0.75rem]"
              >
                <span className="font-mono">{delivery.recipient}</span>
                <span className="text-[var(--color-muted)]">
                  {delivery.provider_code} · {delivery.reference}
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </CardBody>
    </Card>
  );
}

function UssdSimulator({ token }: { token: string }) {
  const [sessionId] = useState(() => `sim-${Date.now()}`);
  const [screen, setScreen] = useState<UssdReply | null>(null);
  const [keypad, setKeypad] = useState("");

  const step = useMutation({
    mutationFn: (input: { message: string; isNew: boolean }) =>
      api.ussdSimulate(token, {
        sessionId,
        msisdn: "233241235993",
        network: 3,
        message: input.message,
        new: input.isNew,
      }),
    onSuccess: (reply) => {
      setScreen(reply);
      setKeypad("");
    },
  });

  const ended = screen !== null && !screen.reply;

  return (
    <Card className="self-start">
      <CardHeader
        title="USSD, live"
        description="The same engine answer, on a feature phone. Dial, choose, read."
        action={
          <DeviceMobile
            aria-hidden
            className="size-4 text-[var(--color-muted)]"
          />
        }
      />
      <CardBody className="space-y-3.5">
        <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-black/60 p-4 font-mono text-small leading-relaxed">
          {screen === null ? (
            <p className="text-[var(--color-muted)]">
              Dial *203*109# to begin.
            </p>
          ) : (
            <p className="whitespace-pre-wrap text-[var(--color-ink)]">
              {screen.message}
            </p>
          )}
        </div>

        {screen === null || ended ? (
          <Button
            onClick={() => step.mutate({ message: "", isNew: true })}
            disabled={step.isPending}
          >
            {ended ? "Dial again" : "Dial *203*109#"}
          </Button>
        ) : (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              step.mutate({ message: keypad, isNew: false });
            }}
            className="flex gap-2"
          >
            <input
              value={keypad}
              onChange={(event) => setKeypad(event.target.value)}
              inputMode="numeric"
              placeholder="Reply"
              className="min-w-0 flex-1 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-raised)] px-3 py-2 font-mono text-small text-[var(--color-ink)]"
            />
            <Button type="submit" disabled={step.isPending || !keypad}>
              Send
            </Button>
          </form>
        )}

        {screen !== null ? (
          <p className="text-[0.6875rem] text-[var(--color-muted)]">
            Session {sessionId} · MTN · this is the same callback Moolre calls
            in production, not a mock.
          </p>
        ) : null}
      </CardBody>
    </Card>
  );
}
