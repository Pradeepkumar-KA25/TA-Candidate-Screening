export interface DashboardStats {
  total_candidates: number;
  last_sync_at: string | null;
  current_shortlist_size: number;
  saved_filter_count: number;
  new_candidates: number;
  shortlisted_candidates: number;
  interview_candidates: number;
  pending_duplicates: number;
  last_sync_status: string | null;
  last_sync_new: number;
  last_sync_updated: number;
  last_sync_errors: number;
  pipeline: DashboardCountItem[];
  source_breakdown: DashboardCountItem[];
  needs_attention: DashboardAttentionItem[];
}

export interface DashboardCountItem {
  label: string;
  count: number;
}

export interface DashboardAttentionItem extends DashboardCountItem {
  route: string;
}

export interface DashboardActivityItem {
  id: string;
  actor_id: string | null;
  action_type: string;
  description: string;
  occurred_at: string;
}

export interface DashboardRecentActivityResponse {
  items: DashboardActivityItem[];
}

export interface DashboardOverview {
  stats: DashboardStats;
  recentActivity: DashboardActivityItem[];
}
