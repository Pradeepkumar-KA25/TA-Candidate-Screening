export interface ProposedFieldChange {
  id: string;
  zoho_field_api_name: string;
  zoho_field_display_name: string;
  existing_zoho_value: Record<string, unknown> | string | null;
  extracted_resume_value: Record<string, unknown> | string | null;
  proposed_value: Record<string, unknown> | string | null;
  change_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  sync_status: 'NOT_SENT' | 'SKIPPED' | 'SYNCED' | 'FAILED';
  sync_error: string | null;
  synced_at: string | null;
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
  write_back_status: 'NOT_SENT' | 'VALIDATED' | 'DISABLED' | 'SYNCED' | 'FAILED';
  write_back_error: string | null;
  write_back_at: string | null;
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
  candidate_total: number;
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

export interface WriteBackPreview {
  candidate_review_id: string;
  zoho_record_id: string;
  payload: Record<string, unknown>;
  skipped: Array<{ field: string; reason: string }>;
  sent_to_zoho: false;
}
