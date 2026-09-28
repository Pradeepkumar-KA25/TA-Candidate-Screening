export interface AuditLogItem {
  id: string;
  actor_id: string | null;
  actor_name: string | null;
  action_type: string;
  description: string;
  entity_type: string | null;
  entity_id: string | null;
  result: string;
  metadata: Record<string, unknown> | null;
  occurred_at: string;
}

export interface AuditLogResponse {
  items: AuditLogItem[];
  total: number;
  page: number;
  page_size: number;
}

export const AUDIT_ACTION_LABELS: Record<string, string> = {
  user_logged_in: 'User signed in',
  user_logged_out: 'User signed out',
  user_created: 'User created',
  user_updated: 'User updated',
  candidate_deleted: 'Candidate deleted',
  candidate_bulk_deleted: 'Candidates deleted in bulk',
  shortlist_candidate_removed: 'Candidate removed from shortlist',
  shortlist_updated: 'Shortlist updated',
  shortlist_export: 'Shortlist exported',
  ranking_executed: 'Candidate ranking executed',
  resume_uploaded: 'Resume uploaded',
  resume_rendered: 'Resume generated',
  resume_deleted: 'Resume deleted',
  resume_enrichment_batch_created: 'Enrichment batch created',
  resume_enrichment_batch_deleted: 'Enrichment batch deleted',
  resume_enrichment_changes_approved: 'Enrichment changes approved',
  resume_enrichment_changes_rejected: 'Enrichment changes rejected',
  sync_started: 'Candidate sync started',
  sync_completed: 'Candidate sync completed',
  sync_failed: 'Candidate sync failed',
  duplicate_reviewed: 'Duplicate review completed',
};
