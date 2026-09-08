import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

/**
 * Centralized API configuration service
 * Provides consistent API base URL across all services
 */
@Injectable({
  providedIn: 'root',
})
export class ApiConfigService {
  /**
   * Get the API base URL for the current environment
   * Development: http://localhost:8000/api/v1
   * Production: /api/v1 (relative path, resolved by proxy/deployment)
   */
  getApiBaseUrl(): string {
    return environment.apiBaseUrl;
  }
}
