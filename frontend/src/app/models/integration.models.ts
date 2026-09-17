export interface ZohoIntegrationStatus {
  integration: string;
  connection_state: 'connected' | 'disconnected';
  status: 'healthy' | 'disconnected' | 'token_expired' | string;
  access_level: string;
  sync_type: string;
  auto_sync_enabled: boolean;
  auto_sync_interval_minutes: number;
  last_successful_sync_at: string | null;
  last_auto_sync_at: string | null;
  last_checked_at: string;
}

export interface AutoSyncSettings {
  auto_sync_enabled: boolean;
  auto_sync_interval_minutes: number;
}
