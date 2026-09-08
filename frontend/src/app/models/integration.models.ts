export interface ZohoIntegrationStatus {
  integration: string;
  connection_state: 'connected' | 'disconnected';
  status: 'healthy' | 'disconnected' | 'token_expired' | string;
  access_level: string;
  sync_type: string;
  last_successful_sync_at: string | null;
  last_checked_at: string;
}
