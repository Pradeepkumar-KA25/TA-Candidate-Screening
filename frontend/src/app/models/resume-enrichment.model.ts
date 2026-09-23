export interface ProposedFieldChange {
  id: string;
  zoho_field_api_name: string;
  zoho_field_display_name: string;
  existing_zoho_value: Record<string, unknown> | string | null;
  extracted_resume_value: Record<string, unknown> | string | null;
  proposed_value: Record<string, unknown> | string | null;
  change_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  field_approval_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CandidateReview {
  id: string;
  batch_id: string;
  candidate_id: string;
  candidate_name: string;
  approval_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  approval_notes: string | null;
  reviewed_by_user_id: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
  proposed_changes: ProposedFieldChange[];
}

export interface ReviewBatch {
  id: string;
  batch_number: string;
  batch_size: number;
  total_candidates: number;
  processed_candidates: number;
  pending_candidates: number;
  approved_candidates: number;
  rejected_candidates: number;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  processing_started_at: string | null;
  processing_completed_at: string | null;
  error_message: string | null;
  created_by_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewBatchDetail extends ReviewBatch {
  candidates: CandidateReview[];
}

export interface ReviewBatchListResponse {
  batches: ReviewBatch[];
  total: number;
  page: number;
  page_size: number;
}

export interface CandidateReviewListResponse {
  candidates: CandidateReview[];
  total: number;
  page: number;
  page_size: number;
}
