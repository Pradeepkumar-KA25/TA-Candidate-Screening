export interface DuplicateCandidateSnapshot {
  id: string;
  zoho_candidate_id: string | null;
  full_name: string;
  email: string | null;
  phone: string | null;
  current_company: string | null;
  current_location: string | null;
  total_experience_years: number | null;
}

export interface DuplicatePairItem {
  id: string;
  match_basis: string;
  confidence: number;
  status: string;
  created_at: string;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  candidate: DuplicateCandidateSnapshot;
  matched_candidate: DuplicateCandidateSnapshot;
}

export interface DuplicateGroupItem {
  jd_id: string | null;
  jd_code: string | null;
  jd_title: string | null;
  duplicate_count: number;
  items: DuplicatePairItem[];
}

export interface DuplicateSummary {
  job_descriptions_reviewed: number;
  possible_duplicates: number;
  no_duplicate_signal: number;
  unassigned_duplicates: number;
}

export interface DuplicateGroupedResponse {
  summary: DuplicateSummary;
  groups: DuplicateGroupItem[];
}
