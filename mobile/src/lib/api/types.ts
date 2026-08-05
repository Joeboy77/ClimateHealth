import type { components } from "./schema";

type Schemas = components["schemas"];

export type RiskLevel = Schemas["RiskLevel"];
export type ConfidenceMode = Schemas["ConfidenceMode"];
export type HealthCondition = Schemas["HealthCondition"];
export type NarrationLanguage = Schemas["NarrationLanguage"];

export type LoginResponse = Schemas["LoginResponse"];
export type CitizenSession = Schemas["CitizenSession"];
export type CitizenIdentity = Schemas["CitizenIdentity"];
export type CitizenRegistration = Schemas["CitizenRegistration"];
export type AgeBand = Schemas["AgeBand"];
export type AgeBandOption = Schemas["AgeBandOption"];
export type GuardianTier = Schemas["GuardianTier"];
export type UserResponse = Schemas["UserResponse"];

export type DistrictSummary = Schemas["DistrictSummaryResponse"];
export type PublicDistrict = Schemas["PublicDistrict"];
export type NearestDistrict = Schemas["NearestDistrict"];
export type DistrictDetail = Schemas["DistrictDetailResponse"];
export type Forecast = Schemas["ForecastResponse"];
export type LagWindow = Schemas["LagWindowResponse"];
export type ForecastRisk = Schemas["ForecastRiskResponse"];
export type Risk = Schemas["RiskResponse"];

export type CommunityReport = Schemas["CommunityReport"];
export type ReportType = Schemas["ReportType"];
export type ReportSubmission = Schemas["ReportSubmission"];

export type DailyQuiz = Schemas["DailyQuiz"];
export type TodaysLesson = Schemas["TodaysLesson"];
export type Lesson = Schemas["Lesson"];
export type QuizResult = Schemas["QuizResult"];
export type GuardianProfile = Schemas["GuardianProfile"];
export type RewardLadder = Schemas["RewardLadder"];
export type GuardianLevel = Schemas["GuardianLevel"];
export type DistrictShield = Schemas["DistrictShield"];
export type PreventionRecord = Schemas["DistrictPreventionRecord"];

/**
 * Condition names arrive as engine identifiers. A citizen is shown ordinary words, and
 * anything we have not named explicitly falls back to something readable rather than to
 * `lassa_fever`.
 */
const CONDITION_WORDS: Partial<Record<string, string>> = {
  malaria: "Malaria",
  cholera: "Cholera",
  meningitis: "Meningitis",
  diarrhoeal_disease: "Diarrhoea",
  respiratory_heat_illness: "Breathing illness",
  dengue: "Dengue",
  typhoid_fever: "Typhoid",
  schistosomiasis: "Bilharzia",
  lassa_fever: "Lassa fever",
  yellow_fever: "Yellow fever",
  leptospirosis: "Leptospirosis",
  trachoma: "Eye infection",
  heat_stroke: "Heat stroke",
  air_pollution_cardiorespiratory: "Air pollution illness",
  child_undernutrition: "Child hunger",
  maternal_heat_outcomes: "Heat harm in pregnancy",
};

export function conditionLabel(condition: string): string {
  const known = CONDITION_WORDS[condition];
  if (known !== undefined) return known;
  const spaced = condition.replace(/_/g, " ");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}
export type RiskList = Schemas["RiskListResponse"];
