"use client";

import { Activity, ArrowRight, Globe, LoaderCircle } from "lucide-react";
import type { Route } from "next";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { GhanaOutline, GHANA_MAP } from "@/components/map/ghana-outline";
import { Button } from "@/components/ui/button";
import { RiskBadge } from "@/components/ui/risk-badge";
import { ApiError } from "@/lib/api/client";
import { RISK_LEVELS } from "@/lib/api/types";
import { useSession } from "@/lib/auth/session";

const DEMO_ACCOUNTS = [
  {
    name: "Akosua Mensah",
    agency: "Ghana Health Service",
    role: "National Surveillance Officer",
    username: "national.officer",
    password: "national-demo-2026",
    scope: "All 260 districts",
  },
  {
    name: "Kwame Boateng",
    agency: "Ghana Health Service",
    role: "District Health Officer",
    username: "madina.officer",
    password: "madina-demo-2026",
    scope: "Madina only",
  },
  {
    name: "Yaa Ofori",
    agency: "Environmental Protection Agency",
    role: "Air Quality Officer",
    username: "epa.officer",
    password: "epa-demo-2026",
    scope: "All 260 districts",
  },
  {
    name: "Ibrahim Alhassan",
    agency: "National Disaster Management Organisation",
    role: "Flood Response Coordinator",
    username: "nadmo.officer",
    password: "nadmo-demo-2026",
    scope: "Madina only",
  },
] as const;

const PLATFORM_QUESTIONS = [
  "Where is health risk rising across the country?",
  "Why is it rising, and how long before cases appear?",
  "What has been assigned, and are we resourced for it?",
] as const;

export default function SignInPage() {
  const router = useRouter();
  const { signIn, status } = useSession();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated") router.replace("/");
  }, [status, router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await signIn(username, password);
      router.replace("/");
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not reach the prediction service.",
      );
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-dvh lg:grid-cols-[minmax(0,4fr)_minmax(0,5fr)]">
      <div className="flex flex-col justify-between px-6 py-8 sm:px-12 lg:px-16">
        <div className="flex items-center gap-2.5">
          <span
            aria-hidden
            className="grid size-8 place-items-center rounded-[var(--radius-md)] bg-[var(--color-accent)]"
          >
            <Activity
              className="size-4 text-[var(--color-accent-ink)]"
              strokeWidth={2.4}
            />
          </span>
          <span className="leading-tight">
            <span className="block text-h3">ClimaHealth Predict</span>
            <span className="block text-[0.6875rem] text-[var(--color-muted)]">
              Agency Command Platform
            </span>
          </span>
        </div>

        <div className="max-w-sm py-12">
          <h1 className="text-h1">Sign in</h1>
          <p className="mt-1.5 text-small text-[var(--color-muted)]">
            Access is scoped to your district or to the whole country.
          </p>

          <form onSubmit={handleSubmit} className="mt-7 space-y-4">
            <Field
              id="username"
              label="Username"
              value={username}
              onChange={setUsername}
              autoComplete="username"
            />
            <Field
              id="password"
              label="Password"
              type="password"
              value={password}
              onChange={setPassword}
              autoComplete="current-password"
            />

            {error ? (
              <p
                role="alert"
                className="rounded-[var(--radius-md)] border border-[var(--color-risk-severe)]/30 bg-[var(--color-risk-severe-surface)] px-3 py-2 text-small text-[var(--color-risk-severe)]"
              >
                {error}
              </p>
            ) : null}

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              disabled={submitting || username === "" || password === ""}
            >
              {submitting ? (
                <LoaderCircle aria-hidden className="size-4 animate-spin" />
              ) : (
                <ArrowRight aria-hidden strokeWidth={2} className="size-4" />
              )}
              {submitting ? "Signing in" : "Sign in"}
            </Button>
          </form>

          <div className="mt-8 border-t border-[var(--color-border)] pt-5">
            <p className="text-micro text-[var(--color-muted)]">Demo access</p>
            <div className="mt-2.5 space-y-1.5">
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.username}
                  type="button"
                  onClick={() => {
                    setUsername(account.username);
                    setPassword(account.password);
                    setError(null);
                  }}
                  className="flex w-full items-center justify-between gap-3 rounded-[var(--radius-md)] border border-[var(--color-border)] px-3 py-2 text-left transition-colors duration-[var(--duration-instant)] hover:border-[var(--color-border-strong)] hover:bg-[var(--color-raised)]"
                >
                  <span className="min-w-0">
                    <span className="block truncate text-small font-medium">
                      {account.name}
                    </span>
                    <span className="block truncate text-[0.6875rem] text-[var(--color-muted)]">
                      {account.agency} · {account.role}
                    </span>
                  </span>
                  <span className="shrink-0 text-right text-[0.6875rem] text-[var(--color-muted)]">
                    {account.scope}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-2.5">
          <Link
            href={"/overview" as Route}
            className="inline-flex items-center gap-1.5 text-small text-[var(--color-accent)] transition-opacity duration-[var(--duration-instant)] hover:opacity-80"
          >
            <Globe aria-hidden strokeWidth={2} className="size-3.5" />
            View the public warning picture without signing in
          </Link>
          <p className="text-[0.6875rem] text-[var(--color-muted)]">
            Climate data from Open-Meteo. Boundaries from geoBoundaries (CC BY
            4.0).
          </p>
        </div>
      </div>

      <aside className="relative hidden overflow-hidden border-l border-[var(--color-border)] bg-[var(--color-raised)] lg:block">
        <svg
          aria-hidden
          viewBox={`0 0 ${GHANA_MAP.viewBox.width} ${GHANA_MAP.viewBox.height}`}
          className="absolute -right-24 top-1/2 h-[130%] -translate-y-1/2 opacity-[0.18]"
        >
          <GhanaOutline
            fill="var(--color-border)"
            stroke="var(--color-canvas)"
            strokeWidth={1}
          />
        </svg>

        <div className="relative flex h-full flex-col justify-center px-16 py-16">
          <p className="text-micro text-[var(--color-muted)]">
            What this platform answers
          </p>
          <ol className="mt-5 max-w-md space-y-4">
            {PLATFORM_QUESTIONS.map((question, index) => (
              <li key={question} className="flex gap-3.5">
                <span className="mt-0.5 font-mono text-small text-[var(--color-accent)]">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="text-h2 font-normal leading-snug">
                  {question}
                </span>
              </li>
            ))}
          </ol>

          <div className="mt-10 max-w-md border-t border-[var(--color-border)] pt-5">
            <p className="text-micro text-[var(--color-muted)]">Risk scale</p>
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {RISK_LEVELS.map((level) => (
                <RiskBadge key={level} level={level} size="sm" />
              ))}
            </div>
            <p className="mt-3 text-small text-[var(--color-muted)]">
              Every level is decided by published epidemiological thresholds,
              and carries the exact conditions that triggered it.
            </p>
          </div>
        </div>
      </aside>
    </div>
  );
}

function Field({
  id,
  label,
  value,
  onChange,
  type = "text",
  autoComplete,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  autoComplete?: string;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-small font-medium">
        {label}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        autoComplete={autoComplete}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1.5 h-9 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-small text-[var(--color-ink)] transition-colors duration-[var(--duration-instant)] placeholder:text-[var(--color-muted)] hover:border-[var(--color-border-strong)]"
      />
    </div>
  );
}
