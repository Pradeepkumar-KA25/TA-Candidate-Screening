export interface SaveFilterRequest {
  name: string;
  jd_id: string | null;
  filter_criteria: Record<string, unknown>;
}

export interface SavedFilterItem {
  id: string;
  recruiter_id: string;
  name: string;
  jd_id: string | null;
  filter_criteria: Record<string, unknown>;
  resolved_query_params: Record<string, string>;
  created_at: string;
  updated_at: string;
  warning: string | null;
}
