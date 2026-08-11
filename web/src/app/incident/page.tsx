"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alarm,
  CalendarDots,
  ClockCounterClockwise,
  Lightning,
  Lock,
  MapPinLine,
  ShieldCheck,
  User,
} from "@phosphor-icons/react";
import { useState } from "react";

import { NationalOperationsMap } from "@/components/map/national-operations-map";
import { OperationsMap } from "@/components/map/operations-map";
import { RequireSession } from "@/components/shell/require-session";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { RiskBadge } from "@/components/ui/risk-badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ACTION_STATUSES,
  ACTION_STATUS_PRESENTATION,
  ACTION_URGENCY_PRESENTATION,
  AGENCY_PRESENTATION,
  ESCALATED_URGENCIES,
  elapsedText,
} from "@/lib/agencies";
import { api } from "@/lib/api/client";
import type {
  ActionStatus,
  ActionTransition,
  IncidentAction,
  UserResponse,
} from "@/lib/api/types";
import { conditionLabel } from "@/lib/api/types";
import { useAuthenticatedSession } from "@/lib/auth/session";
import { cn } from "@/lib/cn";

export default function IncidentRoomPage() {
  return (
    <RequireSession>
      <IncidentRoomEntry />
    </RequireSession>
  );
}

/**
 * A national coordinator opens onto the whole country. A district officer opens
 * straight into their own district, because that is all their scope permits.
 */
function IncidentRoomEntry() {
  const { token, user } = useAuthenticatedSession();
  const scopedDistrictId =
    user?.scope.level === "district" ? user.scope.district_id : null;
  const [chosen, setChosen] = useState<string | null>(null);

  const districtId = scopedDistrictId ?? chosen;

  return (
    <div className="mx-auto max-w-[1600px] px-6 py-6">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--color-border)] pb-6">
        <div>
          <p className="text-eyebrow text-[var(--color-muted)]">
            Incident room
          </p>
          <h1 className="mt-2 text-h1">
            {districtId ? "District response" : "National response board"}
          </h1>
          <p className="mt-1 text-small text-[var(--color-muted)]">
            Who is doing what, where, and how far along they are.
          </p>
        </div>
        {user ? <RoleNotice user={user} /> : null}
      </header>

      <div className="mt-5">
        {districtId ? (
          <>
            {scopedDistrictId === null ? (
              <button
                type="button"
                onClick={() => setChosen(null)}
                className="mb-4 text-small text-[var(--color-accent)] transition-opacity duration-[var(--duration-instant)] hover:opacity-80"
              >
                Back to the national board
              </button>
            ) : null}
            <IncidentRoom token={token} districtId={districtId} />
          </>
        ) : (
          <NationalBoard token={token} onOpenDistrict={setChosen} />
        )}
      </div>
    </div>
  );
}

function RoleNotice({ user }: { user: UserResponse }) {
  return (
    <div className="max-w-sm rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-raised)] px-3 py-2.5">
      <p className="flex items-center gap-1.5 text-micro text-[var(--color-muted)]">
        <ShieldCheck aria-hidden className="size-3.5" />
        {user.role_name}
      </p>
      <p className="mt-1 text-[0.75rem] text-[var(--color-muted)]">
        Most tasks appear on their own: a raised condition triggers every
        agency&rsquo;s standing mandate, so nobody waits to be told.{" "}
        {user.can_assign_actions
          ? "As a coordinator you can also add extra actions and move any status in your scope."
          : `You can move ${user.agency.short_name} tasks. Other agencies own theirs, and a coordinator can add extra work.`}
      </p>
    </div>
  );
}

function NationalBoard({
  token,
  onOpenDistrict,
}: {
  token: string;
  onOpenDistrict: (districtId: string) => void;
}) {
  const [highlighted, setHighlighted] = useState<string | null>(null);

  const actions = useQuery({
    queryKey: ["incident", "national"],
    queryFn: () => api.nationalActions(token),
  });
  const districts = useQuery({
    queryKey: ["districts"],
    queryFn: () => api.districts(token),
  });

  if (actions.isPending || districts.isPending) {
    return (
      <div className="grid gap-5 xl:grid-cols-[minmax(0,5fr)_minmax(0,4fr)]">
        <Skeleton className="h-[640px]" />
        <Skeleton className="h-[640px]" />
      </div>
    );
  }

  const list = actions.data ?? [];
  const byDistrict = new Map<string, IncidentAction[]>();
  for (const action of list) {
    byDistrict.set(action.district_id, [
      ...(byDistrict.get(action.district_id) ?? []),
      action,
    ]);
  }
  const districtNames = new Map(
    (districts.data ?? []).map((d) => [d.district_id, d.name]),
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-5">
        {ACTION_STATUSES.map((status) => {
          const tone = ACTION_STATUS_PRESENTATION[status];
          const count = list.filter((a) => a.status === status).length;
          return (
            <span key={status} className="flex items-baseline gap-2">
              <span
                className="text-metric"
                style={{
                  color: count > 0 ? tone.colour : "var(--color-muted)",
                }}
              >
                {count}
              </span>
              <span className="text-small text-[var(--color-muted)]">
                {tone.label.toLowerCase()}
              </span>
            </span>
          );
        })}
        <EscalationCount actions={list} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,5fr)_minmax(0,4fr)]">
        <Card className="overflow-hidden">
          <CardHeader
            title="Where agencies are working"
            description="Districts with assigned actions are lit. A pulsing ring means something is blocked."
          />
          <div className="aspect-[31/36] bg-[var(--color-canvas)] p-2">
            <NationalOperationsMap
              actions={list}
              districts={districts.data ?? []}
              highlightedDistrictId={highlighted}
              onHighlight={setHighlighted}
              onSelect={onOpenDistrict}
            />
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Districts with active work"
            description="Select one to open its incident room."
          />
          {byDistrict.size === 0 ? (
            <CardBody>
              <p className="text-small text-[var(--color-muted)]">
                No actions are assigned anywhere yet.
              </p>
            </CardBody>
          ) : (
            <ul>
              {[...byDistrict.entries()].map(
                ([districtId, districtActions]) => (
                  <li key={districtId}>
                    <button
                      type="button"
                      onMouseEnter={() => setHighlighted(districtId)}
                      onMouseLeave={() => setHighlighted(null)}
                      onClick={() => onOpenDistrict(districtId)}
                      className={cn(
                        "flex w-full items-center gap-3.5 border-b border-[var(--color-border)] px-5 py-3 text-left last:border-b-0",
                        "transition-colors duration-[var(--duration-instant)] hover:bg-[var(--color-raised)]",
                        highlighted === districtId &&
                          "bg-[var(--color-raised)]",
                      )}
                    >
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-h3">
                          {districtNames.get(districtId) ?? districtId}
                        </span>
                        <span className="block truncate text-[0.75rem] text-[var(--color-muted)]">
                          {[
                            ...new Set(
                              districtActions.map((a) => a.agency_short_name),
                            ),
                          ].join(" · ")}
                        </span>
                        <DistrictEscalation actions={districtActions} />
                      </span>
                      <span className="flex shrink-0 items-center gap-1">
                        {districtActions.map((action) => (
                          <span
                            key={action.action_id}
                            aria-hidden
                            className="size-2 rounded-full"
                            style={{
                              backgroundColor:
                                ACTION_STATUS_PRESENTATION[action.status]
                                  .colour,
                            }}
                          />
                        ))}
                      </span>
                      <span className="w-6 shrink-0 text-right font-mono text-[0.75rem] tabular text-[var(--color-muted)]">
                        {districtActions.length}
                      </span>
                    </button>
                  </li>
                ),
              )}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}

function IncidentRoom({
  token,
  districtId,
}: {
  token: string;
  districtId: string;
}) {
  const { user } = useAuthenticatedSession();
  const queryClient = useQueryClient();
  const [highlighted, setHighlighted] = useState<string | null>(null);

  const room = useQuery({
    queryKey: ["incident", districtId],
    queryFn: () => api.incident(token, districtId),
  });
  const district = useQuery({
    queryKey: ["district", districtId],
    queryFn: () => api.district(token, districtId),
  });
  const reports = useQuery({
    queryKey: ["reports", districtId],
    queryFn: () => api.reports(token, districtId),
  });

  const update = useMutation({
    mutationFn: ({
      actionId,
      status,
    }: {
      actionId: string;
      status: ActionStatus;
    }) => api.updateIncidentAction(token, districtId, actionId, status),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["incident", districtId] }),
  });

  if (room.isPending || district.isPending) {
    return (
      <div className="grid gap-5 xl:grid-cols-[minmax(0,3fr)_minmax(0,4fr)]">
        <Skeleton className="h-[560px]" />
        <Skeleton className="h-[560px]" />
      </div>
    );
  }

  if (room.isError) {
    return (
      <p className="text-small text-[var(--color-muted)]">
        {room.error.message}
      </p>
    );
  }

  const actions = room.data.actions;
  const history = room.data.history;
  const byStatus = ACTION_STATUSES.map((status) => ({
    status,
    count: actions.filter((action) => action.status === status).length,
  }));

  const agencyGroups = [...new Set(actions.map((action) => action.agency))]
    .map((agency) => ({
      agency,
      actions: actions
        .filter((action) => action.agency === agency)
        .sort(
          (first, second) =>
            Number(second.is_lead) - Number(first.is_lead) ||
            first.due_on.localeCompare(second.due_on),
        ),
    }))
    .sort((first, second) => second.actions.length - first.actions.length);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-5">
        {byStatus.map(({ status, count }) => {
          const tone = ACTION_STATUS_PRESENTATION[status];
          return (
            <span key={status} className="flex items-baseline gap-2">
              <span
                className="text-metric"
                style={{
                  color: count > 0 ? tone.colour : "var(--color-muted)",
                }}
              >
                {count}
              </span>
              <span className="text-small text-[var(--color-muted)]">
                {tone.label.toLowerCase()}
              </span>
            </span>
          );
        })}
        <EscalationCount actions={actions} />
        <span className="ml-auto">
          <RiskBadge level={room.data.overall_risk_level} />
        </span>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,3fr)_minmax(0,4fr)]">
        <Card className="overflow-hidden">
          <CardHeader
            title={`${room.data.district_name} operations`}
            description="Markers show tasks with a fixed location. Standing mandates apply district-wide."
          />
          <div className="aspect-[23/20] bg-[var(--color-canvas)] p-2">
            {district.data ? (
              <OperationsMap
                districtId={districtId}
                districtName={district.data.name}
                level={room.data.overall_risk_level}
                centre={{
                  latitude: district.data.latitude,
                  longitude: district.data.longitude,
                }}
                actions={actions}
                reports={reports.data ?? []}
                highlightedActionId={highlighted}
                onHighlight={setHighlighted}
              />
            ) : null}
          </div>
        </Card>

        <div className="space-y-5">
          {agencyGroups.length === 0 ? (
            <Card>
              <CardBody>
                <p className="text-small text-[var(--color-muted)]">
                  Nothing is raised in this district, so no agency has a
                  standing task.
                </p>
              </CardBody>
            </Card>
          ) : (
            agencyGroups.map(({ agency, actions: agencyActions }) => {
              const presentation = AGENCY_PRESENTATION[agency];
              const AgencyIcon = presentation.icon;
              const isMine = user?.agency.code === agency;
              return (
                <Card key={agency}>
                  <CardHeader
                    title={presentation.label}
                    description={`${agencyActions.length} ${
                      agencyActions.length === 1 ? "task" : "tasks"
                    }${isMine ? " · your agency" : ""}`}
                    action={
                      <span
                        aria-hidden
                        className="grid size-8 place-items-center rounded-[var(--radius-md)] border"
                        style={{
                          borderColor: presentation.colour,
                          color: presentation.colour,
                        }}
                      >
                        <AgencyIcon className="size-4" />
                      </span>
                    }
                  />
                  <ul>
                    {agencyActions.map((action) => (
                      <ActionRow
                        key={action.action_id}
                        action={action}
                        history={history.filter(
                          (entry) => entry.action_id === action.action_id,
                        )}
                        highlighted={highlighted === action.action_id}
                        onHover={setHighlighted}
                        onChange={(status) =>
                          update.mutate({ actionId: action.action_id, status })
                        }
                        busy={update.isPending}
                        canMove={
                          user !== null &&
                          (user.can_assign_actions ||
                            user.agency.code === action.agency)
                        }
                      />
                    ))}
                  </ul>
                </Card>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

function ActionRow({
  action,
  history,
  highlighted,
  onHover,
  onChange,
  busy,
  canMove,
}: {
  action: IncidentAction;
  history: ActionTransition[];
  highlighted: boolean;
  onHover: (actionId: string | null) => void;
  onChange: (status: ActionStatus) => void;
  busy: boolean;
  canMove: boolean;
}) {
  const agency = AGENCY_PRESENTATION[action.agency];
  const AgencyIcon = agency.icon;

  return (
    <li
      onMouseEnter={() => onHover(action.action_id)}
      onMouseLeave={() => onHover(null)}
      className={cn(
        "border-b border-[var(--color-border)] px-5 py-3.5 last:border-b-0",
        "transition-colors duration-[var(--duration-instant)]",
        highlighted && "bg-[var(--color-raised)]",
      )}
    >
      <div className="flex items-start gap-3">
        <span
          aria-hidden
          className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-[var(--radius-md)] border"
          style={{ borderColor: agency.colour, color: agency.colour }}
        >
          <AgencyIcon className="size-4" />
        </span>

        <div className="min-w-0 flex-1">
          <p className="flex flex-wrap items-center gap-2">
            <span className="text-small font-medium">{action.description}</span>
            {action.is_lead ? (
              <span
                className="rounded-[var(--radius-sm)] border px-1.5 py-0.5 text-[0.625rem] font-semibold uppercase tracking-wide"
                style={{ borderColor: agency.colour, color: agency.colour }}
              >
                Lead
              </span>
            ) : null}
            <UrgencyChip action={action} />
          </p>
          <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[0.75rem] text-[var(--color-muted)]">
            {action.source_condition ? (
              <span className="flex items-center gap-1">
                <Lightning aria-hidden className="size-3" />
                Triggered by{" "}
                {conditionLabel(action.source_condition).toLowerCase()}
              </span>
            ) : null}
            {action.location_name ? (
              <span className="flex items-center gap-1">
                <MapPinLine aria-hidden className="size-3" />
                {action.location_name}
              </span>
            ) : null}
            <span className="flex items-center gap-1">
              <CalendarDots aria-hidden className="size-3" />
              due {action.due_on}
            </span>
          </p>
          <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[0.6875rem] text-[var(--color-muted)]">
            <span className="flex items-center gap-1">
              <User aria-hidden className="size-3" />
              {action.origin === "playbook"
                ? "Standing mandate, no assignment needed"
                : `Assigned by ${action.assigned_by} on ${action.assigned_on}`}
            </span>
            <span className="flex items-center gap-1">
              <ClockCounterClockwise aria-hidden className="size-3" />
              last moved {elapsedText(action.hours_since_movement)}
            </span>
          </p>

          {history.length > 0 ? (
            <ol className="mt-2 space-y-1 border-l border-[var(--color-border)] pl-3">
              {history.map((entry, index) => (
                <li
                  key={`${entry.action_id}-${index}`}
                  className="text-[0.6875rem] text-[var(--color-muted)]"
                >
                  <span
                    style={{
                      color: ACTION_STATUS_PRESENTATION[entry.to_status].colour,
                    }}
                  >
                    {ACTION_STATUS_PRESENTATION[entry.to_status].label}
                  </span>{" "}
                  by {entry.actor_name} ({entry.actor_agency.toUpperCase()}) ·{" "}
                  {new Date(entry.occurred_at).toLocaleString("en-GB", {
                    day: "2-digit",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </li>
              ))}
            </ol>
          ) : null}
        </div>
      </div>

      <div className="mt-2.5 flex flex-wrap items-center gap-1 pl-11">
        {ACTION_STATUSES.map((status) => {
          const tone = ACTION_STATUS_PRESENTATION[status];
          const selected = action.status === status;
          return (
            <button
              key={status}
              type="button"
              disabled={busy || !canMove}
              title={
                canMove
                  ? undefined
                  : `Only ${action.agency_name} or a coordinator can move this`
              }
              onClick={() => onChange(status)}
              aria-pressed={selected}
              className={cn(
                "rounded-[var(--radius-sm)] border px-2 py-1 text-[0.6875rem]",
                "transition-colors duration-[var(--duration-instant)]",
                selected
                  ? "font-medium"
                  : "border-transparent text-[var(--color-muted)]",
                !selected && canMove && "hover:bg-[var(--color-raised)]",
                !canMove && "cursor-not-allowed opacity-45",
              )}
              style={
                selected
                  ? { borderColor: tone.colour, color: tone.colour }
                  : undefined
              }
            >
              {tone.label}
            </button>
          );
        })}
        {canMove ? null : (
          <span className="ml-1 flex items-center gap-1 text-[0.6875rem] text-[var(--color-muted)]">
            <Lock aria-hidden className="size-3" />
            {action.agency_short_name} owns this
          </span>
        )}
      </div>
    </li>
  );
}

function UrgencyChip({ action }: { action: IncidentAction }) {
  const tone = ACTION_URGENCY_PRESENTATION[action.urgency];
  if (action.urgency === "on_track" || action.urgency === "closed") return null;

  return (
    <span
      title={tone.meaning}
      className="flex items-center gap-1 rounded-[var(--radius-sm)] border px-1.5 py-0.5 text-[0.625rem] font-semibold uppercase tracking-wide"
      style={{ borderColor: tone.colour, color: tone.colour }}
    >
      <Alarm aria-hidden className="size-3" />
      {tone.label}
    </span>
  );
}

function EscalationCount({ actions }: { actions: IncidentAction[] }) {
  const escalated = actions.filter((action) =>
    ESCALATED_URGENCIES.includes(action.urgency),
  );
  if (escalated.length === 0) return null;

  const overdue = escalated.filter(
    (action) => action.urgency === "overdue",
  ).length;

  return (
    <span
      className="flex items-center gap-2 rounded-[var(--radius-md)] border px-2.5 py-1"
      style={{
        borderColor: "var(--color-risk-high)",
        color: "var(--color-risk-high)",
      }}
      title="Overdue means the onset window ran out. Stalled means nobody has touched it in 36 hours."
    >
      <Alarm aria-hidden className="size-3.5" />
      <span className="text-small">
        {overdue > 0 ? `${overdue} overdue` : null}
        {overdue > 0 && escalated.length - overdue > 0 ? " · " : null}
        {escalated.length - overdue > 0
          ? `${escalated.length - overdue} stalled`
          : null}
      </span>
    </span>
  );
}

function DistrictEscalation({ actions }: { actions: IncidentAction[] }) {
  const escalated = actions.filter((action) =>
    ESCALATED_URGENCIES.includes(action.urgency),
  );
  if (escalated.length === 0) return null;

  return (
    <span
      className="mt-0.5 flex items-center gap-1 text-[0.6875rem]"
      style={{ color: "var(--color-risk-high)" }}
    >
      <Alarm aria-hidden className="size-3" />
      {escalated.length === 1
        ? "1 needs attention"
        : `${escalated.length} need attention`}
    </span>
  );
}
