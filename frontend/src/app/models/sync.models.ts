export interface SyncTriggerResponse {
  sync_id: string;
  status: 'running' | 'completed' | 'failed' | string;
}

export interface SyncStatusResponse {
  sync_id: string;
  status: 'running' | 'completed' | 'failed' | string;
  started_at: string;
  completed_at: string | null;
  records_fetched: number;
  records_new: number;
  records_updated: number;
  records_failed: number;
  duplicate_matches: number;
  error_message: string | null;
}

export interface NormalizationExample {
  field: string;
  raw_value: string;
  normalized_value: string;
}

export interface SyncSummaryResponse extends SyncStatusResponse {
  normalized_records: number;
  normalization_examples: NormalizationExample[];
}

export interface SyncHistoryResponse {
  items: SyncStatusResponse[];
}
