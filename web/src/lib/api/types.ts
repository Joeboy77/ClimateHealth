import type { components } from "./schema";

type Schemas = components["schemas"];

export type RiskLevel = Schemas["RiskLevel"];
export type ConfidenceMode = Schemas["ConfidenceMode"];
export type Season = Schemas["Season"];
export type FeatureProvenance = Schemas["FeatureProvenance"];

export type LoginResponse = Schemas["LoginResponse"];
export type UserResponse = Schemas["UserResponse"];
export type ScopeLevel = Schemas["ScopeLevel"];
export type Agency = Schemas["Agency"];
export type AgencyOverview = Schemas["AgencyOverview"];
export type AgencyConditionExposure = Schemas["AgencyConditionExposure"];
export type AgencyResponse = Schemas["AgencyResponse"];

export type DistrictSummary = Schemas["DistrictSummaryResponse"];
export type DistrictDetail = Schemas["DistrictDetailResponse"];
export type ClimateSnapshot = Schemas["ClimateSnapshotResponse"];
export type Risk = Schemas["RiskResponse"];
export type LagWindow = Schemas["LagWindowResponse"];
export type RiskList = Schemas["RiskListResponse"];
export type Forecast = Schemas["ForecastResponse"];
export type ForecastRisk = Schemas["ForecastRiskResponse"];
export type DemoConditions = Schemas["DemoConditionsResponse"];
export type DemoScenario = Schemas["DemoScenario"];
export type Matrix = Schemas["MatrixResponse"];
export type MatrixDriver = Schemas["DriverGroupResponse"];
export type MatrixPathway = Schemas["PathwayResponse"];

export type PreventionLeaderboard = Schemas["PreventionLeaderboard"];
export type PreventionRecord = Schemas["DistrictPreventionRecord"];
export type Distinction = Schemas["Distinction"];
export type PublicOverview = Schemas["PublicOverview"];
export type SmsPreview = Schemas["SmsPreviewResponse"];
export type SmsAlert = Schemas["SmsAlert"];
export type SmsDispatchResult = Schemas["SmsDispatchResult"];
export type UssdReply = Schemas["UssdReply"];
export type WebSocketTicket = Schemas["WebSocketTicket"];
export type NarrationLanguage = Schemas["NarrationLanguage"];
export type PublicDistrictRisk = Schemas["PublicDistrictRisk"];
export type PublicConditionCount = Schemas["PublicConditionCount"];
export type AvertedHazard = Schemas["AvertedHazard"];

export type Alert = Schemas["Alert"];
export type IncidentRoom = Schemas["IncidentRoomResponse"];
export type IncidentAction = Schemas["IncidentActionResponse"];
export type ActionStatus = Schemas["ActionStatus"];
export type ActionOrigin = Schemas["ActionOrigin"];
export type ActionUrgency = Schemas["ActionUrgency"];
export type ActionTransition = Schemas["ActionTransitionResponse"];
export type ReadinessReport = Schemas["ReadinessReport"];
export type ResourceReadiness = Schemas["ResourceReadiness"];
export type ReadinessStatus = Schemas["ReadinessStatus"];

export type CommunityReport = Schemas["CommunityReport"];
export type ReportType = Schemas["ReportType"];
export type VerificationStatus = Schemas["VerificationStatus"];
export type ReportPriority = Schemas["ReportPriority"];
export type CommunitySignal = Schemas["CommunitySignalResponse"];

export type GuardianProfile = Schemas["GuardianProfile"];
export type RewardLadder = Schemas["RewardLadder"];
export type DailyQuiz = Schemas["DailyQuiz"];
export type DistrictShield = Schemas["DistrictShield"];

export const RISK_LEVELS = ["low", "moderate", "high", "severe"] as const;

export const RISK_LEVEL_RANK: Record<RiskLevel, number> = {
  low: 0,
  moderate: 1,
  high: 2,
  severe: 3,
};

export const HEALTH_CONDITION_LABELS: Record<string, string> = {
  malaria: "Malaria",
  cholera: "Cholera",
  meningitis: "Meningitis",
  diarrhoeal_disease: "Diarrhoeal disease",
  respiratory_heat_illness: "Respiratory & heat illness",
  dengue: "Dengue",
  typhoid_fever: "Typhoid fever",
  schistosomiasis: "Schistosomiasis",
  lassa_fever: "Lassa fever",
  yellow_fever: "Yellow fever",
  leptospirosis: "Leptospirosis",
  trachoma: "Trachoma",
  heat_stroke: "Heat stroke",
  air_pollution_cardiorespiratory: "Air pollution illness",
  child_undernutrition: "Child undernutrition",
  maternal_heat_outcomes: "Heat harm in pregnancy",
};

export const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  low: "Low",
  moderate: "Moderate",
  high: "High",
  severe: "Severe",
};

export function conditionLabel(condition: string): string {
  return HEALTH_CONDITION_LABELS[condition] ?? condition;
}
