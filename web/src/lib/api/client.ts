import type {
  AgencyOverview,
  Alert,
  CommunityReport,
  ReportProgress,
  DailyQuiz,
  DemoConditions,
  DistrictDetail,
  DistrictShield,
  DistrictSummary,
  Forecast,
  GuardianProfile,
  IncidentAction,
  IncidentRoom,
  LoginResponse,
  Matrix,
  PreventionLeaderboard,
  PreventionRecord,
  PublicOverview,
  SmsDispatchResult,
  SmsPreview,
  UssdReply,
  WebSocketTicket,
  ReadinessReport,
  RewardLadder,
  RiskList,
  UserResponse,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }

  get isUnauthorised(): boolean {
    return this.status === 401;
  }

  get isForbidden(): boolean {
    return this.status === 403;
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }
}

const MESSAGE_BY_STATUS: Record<number, string> = {
  401: "Your session has expired. Sign in again to continue.",
  403: "Your account is not scoped to this district.",
  404: "We could not find that record.",
  409: "That action has already been recorded.",
  429: "The climate service is rate limiting us. Cached readings are shown until it recovers.",
  503: "Climate data is temporarily unavailable. Try again shortly.",
};

const MAX_DETAIL_LENGTH = 220;

/**
 * Upstream failures sometimes carry a full request URL. Showing that to an
 * officer is noise at best, so fall back to the status message when a detail
 * looks like a raw URL or runs long.
 */
function readableDetail(detail: string): string | null {
  if (detail.length > MAX_DETAIL_LENGTH) return null;
  if (/https?:\/\//.test(detail)) return null;
  return detail;
}

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      const detail = readableDetail(body.detail);
      if (detail) return detail;
    }
  } catch {
    // Response had no JSON body; fall through to the status message.
  }
  return MESSAGE_BY_STATUS[response.status] ?? "Something went wrong.";
}

type RequestOptions = {
  token?: string | null;
  method?: "GET" | "POST" | "DELETE";
  body?: unknown;
  query?: Record<string, string | undefined>;
};

export async function request<T>(
  path: string,
  { token, method = "GET", body, query }: RequestOptions = {},
): Promise<T> {
  const url = new URL(path, API_BASE_URL);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined) url.searchParams.set(key, value);
  }

  const response = await fetch(url, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new ApiError(response.status, await readError(response));
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  login: (username: string, password: string) =>
    request<LoginResponse>("/login", {
      method: "POST",
      body: { username, password },
    }),

  me: (token: string) => request<UserResponse>("/me", { token }),

  /** Published knowledge base. No token: it is epidemiology, not district data. */
  matrix: () => request<Matrix>("/matrix"),

  streamTicket: (token: string) =>
    request<WebSocketTicket>("/ws/ticket", { method: "POST", token }),

  /** The national warning picture, open to anyone. */
  publicOverview: () => request<PublicOverview>("/public/overview"),

  prevention: (token: string) =>
    request<PreventionLeaderboard>("/prevention", { token }),

  preventionRecord: (token: string, districtId: string) =>
    request<PreventionRecord>(`/prevention/${districtId}`, { token }),

  smsPreview: (token: string, districtId: string, language: string) =>
    request<SmsPreview>(`/outreach/sms/${districtId}`, {
      token,
      query: { language },
    }),

  sendSms: (
    token: string,
    districtId: string,
    recipients: string[],
    language: string,
  ) =>
    request<SmsDispatchResult>(`/outreach/sms/${districtId}`, {
      method: "POST",
      token,
      body: { recipients, language },
    }),

  ussdSimulate: (
    token: string,
    session: {
      sessionId: string;
      msisdn: string;
      network: number;
      message: string;
      new: boolean;
    },
  ) =>
    request<UssdReply>("/ussd/simulate", {
      method: "POST",
      token,
      body: { ...session, extension: "109", data: "" },
    }),

  districts: (token: string) =>
    request<DistrictSummary[]>("/districts", { token }),

  district: (token: string, districtId: string) =>
    request<DistrictDetail>(`/districts/${districtId}`, { token }),

  risk: (token: string, districtId: string) =>
    request<RiskList>(`/risk/${districtId}`, { token }),

  forecast: (token: string, districtId: string, language?: string) =>
    request<Forecast>(`/forecast/${districtId}`, {
      token,
      query: { language },
    }),

  alerts: (token: string) => request<Alert[]>("/alerts", { token }),

  agencyOverview: (token: string) =>
    request<AgencyOverview>("/agency/overview", { token }),

  alert: (token: string, alertId: string) =>
    request<Alert>(`/alerts/${alertId}`, { token }),

  incident: (token: string, districtId: string) =>
    request<IncidentRoom>(`/incident/${districtId}`, { token }),

  nationalActions: (token: string) =>
    request<IncidentAction[]>("/incident", { token }),

  assignIncidentAction: (
    token: string,
    districtId: string,
    assignment: {
      agency: string;
      description: string;
      due_on: string;
      location_name?: string;
      latitude?: number;
      longitude?: number;
    },
  ) =>
    request<IncidentAction>(`/incident/${districtId}/assign`, {
      token,
      method: "POST",
      body: assignment,
    }),

  updateIncidentAction: (
    token: string,
    districtId: string,
    actionId: string,
    status: IncidentAction["status"],
  ) =>
    request<IncidentAction>(`/incident/${districtId}/action`, {
      token,
      method: "POST",
      body: { action_id: actionId, status },
    }),

  readiness: (token: string, districtId: string) =>
    request<ReadinessReport>(`/readiness/${districtId}`, { token }),

  reports: (token: string, districtId?: string, reportType?: string) =>
    request<CommunityReport[]>("/reports", {
      token,
      query: { district_id: districtId, report_type: reportType },
    }),

  submitReport: (
    token: string,
    submission: {
      district_id: string;
      report_type: string;
      note: string;
      latitude?: number;
      longitude?: number;
    },
  ) =>
    request<CommunityReport>("/reports", {
      token,
      method: "POST",
      body: submission,
    }),

  reportProgress: (token: string, reportId: string) =>
    request<ReportProgress>(`/reports/${reportId}/progress`, { token }),

  advanceReportStage: (
    token: string,
    reportId: string,
    stage: string,
    note: string | null,
  ) =>
    request<ReportProgress>(`/reports/${reportId}/stage`, {
      method: "POST",
      token,
      body: { stage, note },
    }),

  verifyReport: (
    token: string,
    reportId: string,
    status: string,
    priority = "routine",
  ) =>
    request<CommunityReport>(`/reports/${reportId}/verify`, {
      token,
      method: "POST",
      body: { status, priority },
    }),

  guardian: (token: string, userId: string) =>
    request<GuardianProfile>(`/guardian/${userId}`, { token }),

  rewards: (token: string, userId: string) =>
    request<RewardLadder>(`/rewards/${userId}`, { token }),

  dailyQuiz: (token: string, districtId: string) =>
    request<DailyQuiz>(`/quiz/daily/${districtId}`, { token }),

  shield: (token: string, districtId: string) =>
    request<DistrictShield>(`/shield/${districtId}`, { token }),

  setDemoConditions: (token: string, districtId: string, scenario: string) =>
    request<DemoConditions>("/demo/set-conditions", {
      token,
      method: "POST",
      body: { district_id: districtId, scenario },
    }),

  clearDemoConditions: (token: string, districtId: string) =>
    request<void>(`/demo/set-conditions/${districtId}`, {
      token,
      method: "DELETE",
    }),
};
