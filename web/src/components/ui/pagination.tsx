"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { cn } from "@/lib/cn";

export function Pagination({
  page,
  pageCount,
  total,
  itemLabel,
  onChange,
}: {
  page: number;
  pageCount: number;
  total: number;
  itemLabel: string;
  onChange: (page: number) => void;
}) {
  if (pageCount <= 1) return null;

  return (
    <nav
      aria-label={`${itemLabel} pages`}
      className="flex items-center justify-between gap-3 border-t border-[var(--color-border)] px-5 py-2.5"
    >
      <p className="text-[0.75rem] text-[var(--color-muted)]">
        Page <span className="tabular">{page}</span> of{" "}
        <span className="tabular">{pageCount}</span> ·{" "}
        <span className="tabular">{total}</span> {itemLabel}
      </p>
      <div className="flex items-center gap-1">
        <PageButton
          label="Previous page"
          disabled={page === 1}
          onClick={() => onChange(page - 1)}
        >
          <ChevronLeft aria-hidden strokeWidth={2} className="size-4" />
        </PageButton>
        <PageButton
          label="Next page"
          disabled={page === pageCount}
          onClick={() => onChange(page + 1)}
        >
          <ChevronRight aria-hidden strokeWidth={2} className="size-4" />
        </PageButton>
      </div>
    </nav>
  );
}

function PageButton({
  label,
  disabled,
  onClick,
  children,
}: {
  label: string;
  disabled: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "grid size-7 place-items-center rounded-[var(--radius-md)] border border-[var(--color-border)]",
        "transition-colors duration-[var(--duration-instant)]",
        disabled
          ? "cursor-default text-[var(--color-border-strong)]"
          : "text-[var(--color-muted)] hover:border-[var(--color-border-strong)] hover:bg-[var(--color-raised)] hover:text-[var(--color-ink)]",
      )}
    >
      {children}
    </button>
  );
}
