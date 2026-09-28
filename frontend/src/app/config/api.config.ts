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
    * The relative path is resolved by the Angular development proxy locally
    * and by Nginx in deployed containers.
   */
  getApiBaseUrl(): string {
    return environment.apiBaseUrl;
  }
}
