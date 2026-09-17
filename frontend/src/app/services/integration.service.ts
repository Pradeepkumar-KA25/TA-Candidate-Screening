import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, catchError, finalize, of, switchMap, tap, timer } from 'rxjs';

import { AutoSyncSettings, ZohoIntegrationStatus } from '../models/integration.models';
import { ApiConfigService } from '../config/api.config';

@Injectable({
  providedIn: 'root',
})
export class IntegrationService {
  private apiBaseUrl: string;

  private readonly statusSubject = new BehaviorSubject<ZohoIntegrationStatus>(this.buildFallbackStatus());
  private readonly loadingSubject = new BehaviorSubject<boolean>(false);
  private readonly errorSubject = new BehaviorSubject<string | null>(null);

  readonly status$ = this.statusSubject.asObservable();
  readonly loading$ = this.loadingSubject.asObservable();
  readonly error$ = this.errorSubject.asObservable();

  constructor(
    private readonly httpClient: HttpClient,
    private readonly apiConfig: ApiConfigService
  ) {
    this.apiBaseUrl = this.apiConfig.getApiBaseUrl();
  }

  getZohoStatus(): Observable<ZohoIntegrationStatus> {
    this.loadingSubject.next(true);

    return this.httpClient.get<ZohoIntegrationStatus>(`${this.apiBaseUrl}/integrations/zoho/status`).pipe(
      tap((status) => {
        this.statusSubject.next(status);
        this.errorSubject.next(null);
      }),
      catchError(() => {
        const fallback = this.buildFallbackStatus();
        this.statusSubject.next(fallback);
        this.errorSubject.next('Unable to fetch Zoho Recruit connection status');
        return of(fallback);
      }),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  updateAutoSyncSettings(settings: AutoSyncSettings): Observable<ZohoIntegrationStatus> {
    this.loadingSubject.next(true);

    return this.httpClient.put<ZohoIntegrationStatus>(`${this.apiBaseUrl}/integrations/zoho/auto-sync`, settings).pipe(
      tap((status) => {
        this.statusSubject.next(status);
        this.errorSubject.next(null);
      }),
      catchError((error) => {
        this.errorSubject.next('Unable to update auto-sync settings');
        throw error;
      }),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  pollZohoStatus(intervalMs: number = 30000): Observable<ZohoIntegrationStatus> {
    return timer(0, intervalMs).pipe(switchMap(() => this.getZohoStatus()));
  }

  private buildFallbackStatus(): ZohoIntegrationStatus {
    return {
      integration: 'Zoho Recruit',
      connection_state: 'disconnected',
      status: 'disconnected',
      access_level: 'read_only',
      sync_type: 'manual',
      auto_sync_enabled: false,
      auto_sync_interval_minutes: 5,
      last_successful_sync_at: null,
      last_auto_sync_at: null,
      last_checked_at: new Date().toISOString(),
    };
  }
}

