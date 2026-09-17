export interface CandidateListItem {
  id: string;
  zoho_candidate_id: string;
  full_name: string;
  skills: string[] | null;
  total_experience_years: number | null;
  current_location: string | null;
  current_company: string | null;
  notice_period_days: number | null;
  status: string;
  match_percentage: number | null;
  updated_at: string;
}

export interface CandidateListResponse {
  items: CandidateListItem[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  q: string | null;
  sort_by: string;
  sort_order: 'asc' | 'desc';
}

export interface CandidateListQuery {
  q?: string;
  page: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  jdId?: string;
  skills?: string[];
  experienceMin?: number;
  experienceMax?: number;
  location?: string;
  preferredLocation?: string;
  noticePeriodMax?: number;
  status?: string;
  degree?: string;
  certification?: string;
  resumeUpdatedSince?: number;
  source?: string;
  relevantExperience?: number;
  currentCtc?: number;
  expectedCtc?: number;
  previousCompany?: string;
  employmentStatus?: string;
}

export interface CandidateNormalizedPair {
  field: string;
  raw_value: string;
  normalized_value: string;
}

export interface CandidateMatchContext {
  jd_id: string | null;
  jd_title: string | null;
  match_percentage: number | null;
  match_score: number | null;
  matched_criteria: string[] | null;
  metadata: Record<string, unknown> | null;
}

export interface CandidateExtendedFields {
  personal_contact: Record<string, string>;
  employment: Record<string, string>;
  interview_process: Record<string, string>;
  candidate_lifecycle: Record<string, string>;
  salary_benefits: Record<string, string>;
  referral_vendor_sourcing: Record<string, string>;
}

export interface CandidateDetailResponse {
  id: string;
  zoho_candidate_id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  total_experience_years: number | null;
  relevant_experience_years: number | null;
  current_company: string | null;
  current_location: string | null;
  preferred_location: string | null;
  notice_period_days: number | null;
  skills: string[] | null;
  degree: string | null;
  normalized_degree: string | null;
  current_ctc: number | null;
  expected_ctc: number | null;
  status: string;
  source: string;
  created_at: string;
  updated_at: string;
  normalized_data: CandidateNormalizedPair[];
  match_context: CandidateMatchContext;
  extended_fields: CandidateExtendedFields;
}
