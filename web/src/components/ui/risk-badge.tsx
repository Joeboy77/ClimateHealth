import type { RiskLevel } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { riskPresentation } from "@/lib/risk";

type RiskBadgeProps = {
  level: RiskLevel;
  size?: "sm" | "md";
  showIcon?: boolean;
  className?: string;
};

export function RiskBadge({
  level,
  size = "md",
  showIcon = true,
  className,
}: RiskBadgeProps) {
  const {
    label,
    icon: Icon,
    foreground,
    surface,
    border,
  } = riskPresentation(level);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-[var(--radius-sm)] border font-medium",
        size === "sm" ? "px-1.5 py-0.5 text-[0.6875rem]" : "px-2 py-1 text-xs",
        surface,
        border,
        foreground,
        className,
      )}
    >
      {showIcon ? (
        <Icon
          aria-hidden
          strokeWidth={2}
          className={size === "sm" ? "size-3" : "size-3.5"}
        />
      ) : null}
      {label}
    </span>
  );
}
