import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, catchError, finalize, forkJoin, map, of, tap } from 'rxjs';

import { DashboardActivityItem, DashboardOverview, DashboardRecentActivityResponse, DashboardStats } from '../models/dashboard.models';
import { ApiConfigService } from '../config/api.config';

@Injectable({
  providedIn: 'root',
})
export class DashboardService {
  private apiBaseUrl: string;

  private readonly statsSubject = new BehaviorSubject<DashboardStats | null>(null);
  private readonly recentActivitySubject = new BehaviorSubject<DashboardActivityItem[]>([]);
  private readonly loadingSubject = new BehaviorSubject<boolean>(false);
  private readonly errorSubject = new BehaviorSubject<string | null>(null);

  readonly stats$ = this.statsSubject.asObservable();
  readonly recentActivity$ = this.recentActivitySubject.asObservable();
  readonly loading$ = this.loadingSubject.asObservable();
  readonly error$ = this.errorSubject.asObservable();

  constructor(
    private readonly httpClient: HttpClient,
    private readonly apiConfig: ApiConfigService
  ) {
    this.apiBaseUrl = this.apiConfig.getApiBaseUrl();
  }

  loadDashboardOverview(limit: number = 4): Observable<DashboardOverview> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    return forkJoin({
      stats: this.getDashboardStats(),
      recentActivity: this.getRecentActivity(limit),
    }).pipe(
      tap(({ stats, recentActivity }) => {
        this.statsSubject.next(stats);
        this.recentActivitySubject.next(recentActivity.items);
        this.errorSubject.next(null);
      }),
      map(({ stats, recentActivity }) => ({ stats, recentActivity: recentActivity.items })),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  getDashboardStats(): Observable<DashboardStats> {
    return this.httpClient.get<DashboardStats>(`${this.apiBaseUrl}/dashboard/stats`).pipe(
      catchError((error) => {
        this.errorSubject.next(error?.error?.message || 'Unable to load dashboard stats');
        return of({
          total_candidates: 0,
          last_sync_at: null,
          current_shortlist_size: 0,
          saved_filter_count: 0,
          new_candidates: 0,
          shortlisted_candidates: 0,
          interview_candidates: 0,
          pending_duplicates: 0,
          last_sync_status: null,
          last_sync_new: 0,
          last_sync_updated: 0,
          last_sync_errors: 0,
          pipeline: [],
          source_breakdown: [],
          needs_attention: [],
        });
      })
    );
  }

  getRecentActivity(limit: number = 4): Observable<DashboardRecentActivityResponse> {
    return this.httpClient.get<DashboardRecentActivityResponse>(`${this.apiBaseUrl}/dashboard/recent-activity`, {
      params: { limit: String(limit) },
    }).pipe(
      catchError((error) => {
        this.errorSubject.next(error?.error?.message || 'Unable to load recent activity');
        return of({ items: [] });
      })
    );
  }
}
