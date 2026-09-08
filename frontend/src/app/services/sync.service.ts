import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, catchError, filter, map, of, switchMap, takeWhile, tap, timer } from 'rxjs';

import { SyncHistoryResponse, SyncStatusResponse, SyncSummaryResponse, SyncTriggerResponse } from '../models/sync.models';
import { ApiConfigService } from '../config/api.config';

@Injectable({
  providedIn: 'root',
})
export class SyncService {
  private apiBaseUrl: string;

  private readonly loadingSubject = new BehaviorSubject<boolean>(false);
  private readonly errorSubject = new BehaviorSubject<string | null>(null);

  readonly loading$ = this.loadingSubject.asObservable();
  readonly error$ = this.errorSubject.asObservable();

  constructor(
    private readonly httpClient: HttpClient,
    private readonly apiConfig: ApiConfigService
  ) {
    this.apiBaseUrl = this.apiConfig.getApiBaseUrl();
  }

  startCandidateSync(): Observable<SyncTriggerResponse> {
    this.loadingSubject.next(true);

    return this.httpClient.post<SyncTriggerResponse>(`${this.apiBaseUrl}/sync/candidates`, {}).pipe(
      tap(() => {
        this.errorSubject.next(null);
      }),
      catchError((error) => {
        const errorMessage =
          error?.error?.message ||
          (error?.status === 409 ? 'A candidate sync is already running. Please wait.' : 'Failed to start candidate sync.');
        this.errorSubject.next(errorMessage);
        return of({ sync_id: '', status: 'failed' });
      }),
      tap(() => this.loadingSubject.next(false))
    );
  }

  getSyncStatus(syncId: string): Observable<SyncStatusResponse> {
    return this.httpClient.get<SyncStatusResponse>(`${this.apiBaseUrl}/sync/${syncId}`);
  }

  getSyncSummary(syncId: string): Observable<SyncSummaryResponse> {
    return this.httpClient.get<SyncSummaryResponse>(`${this.apiBaseUrl}/sync/${syncId}/summary`);
  }

  getSyncHistory(limit: number = 6): Observable<SyncHistoryResponse> {
    return this.httpClient.get<SyncHistoryResponse>(`${this.apiBaseUrl}/sync/history`, {
      params: { limit: String(limit) },
    });
  }

  trackSyncUntilDone(syncId: string, intervalMs: number = 1500): Observable<SyncStatusResponse> {
    return timer(0, intervalMs).pipe(
      switchMap(() => this.getSyncStatus(syncId)),
      takeWhile((status) => status.status === 'running', true),
      filter((status) => status.sync_id === syncId)
    );
  }

  buildFriendlyError(status: SyncStatusResponse): string | null {
    if (status.status !== 'failed') {
      return null;
    }

    return status.error_message || 'Candidate sync failed. Please try again.';
  }
}
