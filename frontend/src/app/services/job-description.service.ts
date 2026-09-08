import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, catchError, finalize, map, of, shareReplay, switchMap, tap } from 'rxjs';

import { CreateJobDescriptionRequest, JobDescriptionListItem, JobDescriptionResponse } from '../models/job-description.models';
import { ApiConfigService } from '../config/api.config';

@Injectable({
  providedIn: 'root',
})
export class JobDescriptionService {
  private apiBaseUrl: string;

  private readonly loadingSubject = new BehaviorSubject<boolean>(false);
  private readonly errorSubject = new BehaviorSubject<string | null>(null);
  private cachedRequest$: Observable<JobDescriptionListItem[]> | null = null;

  readonly loading$ = this.loadingSubject.asObservable();
  readonly error$ = this.errorSubject.asObservable();

  constructor(
    private readonly httpClient: HttpClient,
    private readonly apiConfig: ApiConfigService
  ) {
    this.apiBaseUrl = this.apiConfig.getApiBaseUrl();
  }

  listJobDescriptions(forceRefresh: boolean = false): Observable<JobDescriptionListItem[]> {
    if (forceRefresh || this.cachedRequest$ === null) {
      this.loadingSubject.next(true);

      this.cachedRequest$ = this.httpClient
        .get<JobDescriptionListItem[]>(`${this.apiBaseUrl}/job-descriptions`)
        .pipe(
          tap(() => this.errorSubject.next(null)),
          catchError(() => {
            this.errorSubject.next('Unable to load job descriptions');
            return of([]);
          }),
          finalize(() => this.loadingSubject.next(false)),
          shareReplay({ bufferSize: 1, refCount: false })
        );
    }

    return this.cachedRequest$;
  }

  createJobDescription(request: CreateJobDescriptionRequest): Observable<JobDescriptionResponse | null> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    return this.httpClient.post<JobDescriptionResponse>(`${this.apiBaseUrl}/job-descriptions`, request).pipe(
      switchMap((created) =>
        this.listJobDescriptions(true).pipe(
          map(() => created)
        )
      ),
      catchError((error) => {
        this.errorSubject.next(error?.error?.message || 'Unable to create job description');
        return of(null);
      }),
      finalize(() => this.loadingSubject.next(false))
    );
  }
}
