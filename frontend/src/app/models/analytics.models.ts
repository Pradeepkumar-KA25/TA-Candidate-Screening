export interface AnalyticsPoint {
  label: string;
  value: number;
}

export interface DashboardAnalytics {
  days: number;
  candidate_growth: AnalyticsPoint[];
  pipeline: AnalyticsPoint[];
  sources: AnalyticsPoint[];
  sync_outcomes: AnalyticsPoint[];
  enrichment_outcomes: AnalyticsPoint[];
  activity_by_action: AnalyticsPoint[];
}
