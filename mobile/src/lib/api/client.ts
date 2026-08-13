import Constants from "expo-constants";

import type {
  AgeBandOption,
  CitizenIdentity,
  CitizenLogin,
  ReportProgress,
  CitizenRegistration,
  CitizenSession,
  CommunityReport,
  DailyQuiz,
  DistrictDetail,
  DistrictShield,
  DistrictSummary,
  NearestDistrict,
  PublicDistrict,
  Forecast,
  GuardianProfile,
  LoginResponse,
  QuizResult,
  PreventionRecord,
  QuizSession,
  NhisRenewal,
  RenewalQuote,
  ReportSubmission,
  SessionResult,
  RiskList,
  RewardLadder,
  TodaysLesson,
  UserResponse,
} from "./types";

/**
 * A phone is not on localhost. In development the API host is read from the Expo dev
 * server's own address, so a real device on the same network reaches the backend without
 * anybody editing a constant.
 */
function inferDevelopmentHost(): string | null {
  const hostUri =
    Constants.expoConfig?.hostUri ??
    (Constants.expoGoConfig as { debuggerHost?: string } | undefined)?.debuggerHost;
  if (!hostUri) return null;
  const host = hostUri.split(":")[0];
  return host ? `http://${host}:8000` : null;
}

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ??
  inferDevelopmentHost() ??
  "http://127.0.0.1:8000";

export const REQUEST_TIMEOUT_MS = 20_000;

type SessionExpiredListener = () => void;
const sessionExpiredListeners = new Set<SessionExpiredListener>();

export function addSessionExpiredListener(
  listener: SessionExpiredListener,
): () => void {
  sessionExpiredListeners.add(listener);
  return () => {
    sessionExpiredListeners.delete(listener);
  };
}

function notifySessionExpired(): void {
  for (const listener of sessionExpiredListeners) {
    listener();
  }
}

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export class OfflineError extends Error {
  constructor() {
    super("No connection. Showing what was last saved on this phone.");
    this.name = "OfflineError";
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "DELETE";
  token?: string;
  body?: unknown;
  query?: Record<string, string | undefined>;
};

/**
 * Never surface a raw provider message or a URL to a citizen. They cannot act on it, and
 * a warning app that prints a stack trace has stopped being trustworthy.
 */
async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    const detail = typeof body.detail === "string" ? body.detail : null;
    if (detail && !detail.includes("http")) return detail;
  } catch {
    // Fall through to the generic message.
  }
  return response.status >= 500
    ? "The service is having trouble. Try again shortly."
    : "That did not work. Try again.";
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", token, body, query } = options;

  const url = new URL(path, API_BASE_URL);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined) url.searchParams.set(key, value);
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url.toString(), {
      method,
      signal: controller.signal,
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token !== undefined ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    });

    if (!response.ok) {
      if (response.status === 401) {
        notifySessionExpired();
      }
      throw new ApiError(response.status, await readError(response));
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new OfflineError();
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  login: (username: string, password: string) =>
    request<LoginResponse>("/login", { method: "POST", body: { username, password } }),

  me: (token: string) => request<UserResponse>("/me", { token }),

  /** Open: the sign-up screen renders before anybody has an account. */
  ageBands: () => request<AgeBandOption[]>("/citizens/age-bands"),

  publicDistricts: () => request<PublicDistrict[]>("/public/districts"),

  nearestDistrict: (latitude: number, longitude: number) =>
    request<NearestDistrict>("/public/districts/nearest", {
      query: { latitude: String(latitude), longitude: String(longitude) },
    }),

  registerCitizen: (registration: CitizenRegistration) =>
    request<CitizenSession>("/citizens", { method: "POST", body: registration }),

  signInCitizen: (login: CitizenLogin) =>
    request<CitizenSession>("/citizens/login", { method: "POST", body: login }),

  reports: (token: string, districtId: string) =>
    request<CommunityReport[]>("/reports", {
      token,
      query: { district_id: districtId },
    }),

  reportProgress: (token: string, reportId: string) =>
    request<ReportProgress>(`/reports/${reportId}/progress`, { token }),

  citizen: (token: string) => request<CitizenIdentity>("/citizens/me", { token }),

  risk: (token: string, districtId: string) =>
    request<RiskList>(`/risk/${districtId}`, { token }),

  preventionRecord: (token: string, districtId: string) =>
    request<PreventionRecord>(`/prevention/${districtId}`, { token }),

  quizSession: (token: string, districtId: string) =>
    request<QuizSession>(`/play/session/${districtId}`, { token }),

  submitSession: (
    token: string,
    userId: string,
    answers: { question_id: string; selected_option_index: number }[],
  ) =>
    request<SessionResult>("/play/session", {
      method: "POST",
      token,
      body: { user_id: userId, answers },
    }),

  rewardQuote: (token: string, userId: string) =>
    request<RenewalQuote>(`/rewards/quote/${userId}`, { token }),

  claimNhisRenewal: (token: string, userId: string) =>
    request<NhisRenewal>("/rewards/redeem", {
      method: "POST",
      token,
      body: { user_id: userId },
    }),

  lessonToday: (token: string, districtId: string) =>
    request<TodaysLesson>(`/lessons/today/${districtId}`, { token }),

  submitReport: (token: string, submission: ReportSubmission) =>
    request<CommunityReport>("/reports", { method: "POST", token, body: submission }),

  districts: (token: string) => request<DistrictSummary[]>("/districts", { token }),

  district: (token: string, districtId: string) =>
    request<DistrictDetail>(`/districts/${districtId}`, { token }),

  forecast: (token: string, districtId: string, language?: string) =>
    request<Forecast>(`/forecast/${districtId}`, { token, query: { language } }),

  dailyQuiz: (token: string, districtId: string) =>
    request<DailyQuiz>(`/quiz/daily/${districtId}`, { token }),

  answerQuiz: (
    token: string,
    userId: string,
    questionId: string,
    selectedOptionIndex: number,
  ) =>
    request<QuizResult>("/quiz/answer", {
      method: "POST",
      token,
      body: {
        user_id: userId,
        question_id: questionId,
        selected_option_index: selectedOptionIndex,
      },
    }),

  guardian: (token: string, userId: string) =>
    request<GuardianProfile>(`/guardian/${userId}`, { token }),

  rewards: (token: string, userId: string) =>
    request<RewardLadder>(`/rewards/${userId}`, { token }),

  shield: (token: string, districtId: string) =>
    request<DistrictShield>(`/shield/${districtId}`, { token }),
} as const;

/**
 * A photograph is sent as the whole request body rather than as a form field: one image
 * per request needs no field names, and it is uploaded before the report so that a weak
 * connection retries the bytes and not the whole submission.
 */
export async function uploadReportPhoto(token: string, uri: string): Promise<string> {
  const file = await fetch(uri);
  const blob = await file.blob();

  const response = await fetch(new URL("/reports/photo", API_BASE_URL).toString(), {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": blob.type || "image/jpeg",
    },
    body: blob,
  });

  if (!response.ok) throw new ApiError(response.status, await readError(response));
  return ((await response.json()) as { photo_reference: string }).photo_reference;
}
