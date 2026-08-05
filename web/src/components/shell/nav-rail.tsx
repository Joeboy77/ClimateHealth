"use client";

import {
  Activity,
  BellRing,
  ClipboardList,
  LayoutGrid,
  MapPin,
  MessageSquareWarning,
  Network,
  PackageCheck,
  PanelLeftClose,
  PanelLeftOpen,
  Smartphone,
  type LucideIcon,
} from "lucide-react";
import type { Route } from "next";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useSession } from "@/lib/auth/session";
import { cn } from "@/lib/cn";

type NavItem = {
  href: Route;
  label: string;
  icon: LucideIcon;
  matchPrefix?: string;
};

function itemsForScope(districtId: string | null): readonly NavItem[] {
  const home: NavItem = districtId
    ? {
        href: `/districts/${districtId}` as Route,
        label: "My district",
        icon: MapPin,
        matchPrefix: "/districts",
      }
    : { href: "/" as Route, label: "National picture", icon: LayoutGrid };

  return [
    home,
    { href: "/alerts" as Route, label: "Alerts", icon: BellRing },
    { href: "/incident" as Route, label: "Incident room", icon: ClipboardList },
    { href: "/readiness" as Route, label: "Readiness", icon: PackageCheck },
    {
      href: "/reports" as Route,
      label: "Field reports",
      icon: MessageSquareWarning,
    },
    { href: "/outreach" as Route, label: "Outreach", icon: Smartphone },
    { href: "/matrix" as Route, label: "Pathway matrix", icon: Network },
  ];
}

function isActive(pathname: string, item: NavItem): boolean {
  const prefix = item.matchPrefix ?? item.href;
  if (prefix === "/") return pathname === "/";
  return pathname.startsWith(prefix);
}

export function NavRail({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  const pathname = usePathname();
  const { user } = useSession();
  const districtId =
    user?.scope.level === "district" ? (user.scope.district_id ?? null) : null;

  return (
    <nav
      aria-label="Primary"
      className={cn(
        "flex h-full shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]",
        "transition-[width] duration-[var(--duration-medium)] ease-[var(--ease-out)]",
        collapsed ? "w-[60px]" : "w-56",
      )}
    >
      <div
        className={cn(
          "flex items-center gap-2.5 px-3.5 py-4",
          collapsed && "justify-center px-0",
        )}
      >
        <span
          aria-hidden
          className="grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--color-accent)]"
        >
          <Activity
            className="size-4 text-[var(--color-accent-ink)]"
            strokeWidth={2.4}
          />
        </span>
        {collapsed ? null : (
          <span className="min-w-0 leading-tight">
            <span className="block truncate text-h3 text-[var(--color-ink)]">
              ClimaHealth
            </span>
            <span className="block truncate text-[0.6875rem] text-[var(--color-muted)]">
              Command Platform
            </span>
          </span>
        )}
      </div>

      <ul className="flex flex-1 flex-col gap-0.5 px-2 py-2">
        {itemsForScope(districtId).map((item) => {
          const active = isActive(pathname, item);
          const Icon = item.icon;
          return (
            <li key={item.label}>
              <Link
                href={item.href}
                aria-current={active ? "page" : undefined}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "flex items-center gap-2.5 rounded-[var(--radius-md)] py-2",
                  "text-small transition-colors duration-[var(--duration-instant)]",
                  collapsed ? "justify-center px-0" : "px-2.5",
                  active
                    ? "bg-[var(--color-accent-subtle)] font-medium text-[var(--color-accent)]"
                    : "text-[var(--color-muted)] hover:bg-[var(--color-raised)] hover:text-[var(--color-ink)]",
                )}
              >
                <Icon aria-hidden strokeWidth={2} className="size-4 shrink-0" />
                {collapsed ? (
                  <span className="sr-only">{item.label}</span>
                ) : (
                  item.label
                )}
              </Link>
            </li>
          );
        })}
      </ul>

      {user ? <AgencyCard user={user} collapsed={collapsed} /> : null}

      <button
        type="button"
        onClick={onToggle}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        aria-expanded={!collapsed}
        className={cn(
          "flex items-center gap-2.5 border-t border-[var(--color-border)] py-2.5",
          "text-[0.75rem] text-[var(--color-muted)] transition-colors duration-[var(--duration-instant)]",
          "hover:bg-[var(--color-raised)] hover:text-[var(--color-ink)]",
          collapsed ? "justify-center px-0" : "px-3.5",
        )}
      >
        {collapsed ? (
          <PanelLeftOpen aria-hidden strokeWidth={2} className="size-4" />
        ) : (
          <>
            <PanelLeftClose aria-hidden strokeWidth={2} className="size-4" />
            Collapse
          </>
        )}
      </button>
    </nav>
  );
}

function AgencyCard({
  user,
  collapsed,
}: {
  user: NonNullable<ReturnType<typeof useSession>["user"]>;
  collapsed: boolean;
}) {
  const initials = user.display_name
    .split(" ")
    .map((part) => part.charAt(0))
    .slice(0, 2)
    .join("");

  return (
    <div
      className={cn(
        "mx-2 mb-2 flex items-center gap-2.5 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-raised)] py-2",
        collapsed ? "justify-center px-0" : "px-2.5",
      )}
      title={
        collapsed ? `${user.display_name} — ${user.agency.name}` : undefined
      }
    >
      <span
        aria-hidden
        className="grid size-7 shrink-0 place-items-center rounded-full bg-[var(--color-accent)] text-[0.6875rem] font-semibold text-[var(--color-accent-ink)]"
      >
        {initials}
      </span>
      {collapsed ? null : (
        <span className="min-w-0 leading-tight">
          <span className="block truncate text-[0.8125rem] font-medium text-[var(--color-ink)]">
            {user.display_name}
          </span>
          <span className="block truncate text-[0.6875rem] text-[var(--color-muted)]">
            {user.agency.short_name} · {user.job_title}
          </span>
        </span>
      )}
    </div>
  );
}
