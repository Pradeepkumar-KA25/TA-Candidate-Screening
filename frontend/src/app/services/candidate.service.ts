import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, catchError, finalize, of, tap } from 'rxjs';

import { CandidateDetailResponse, CandidateListQuery, CandidateListResponse } from '../models/candidate.models';
import { ApiConfigService } from '../config/api.config';

@Injectable({
  providedIn: 'root',
})
export class CandidateService {
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

  loadCandidates(query: CandidateListQuery): Observable<CandidateListResponse> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    const params: Record<string, string> = {
      page: String(query.page),
      page_size: String(query.pageSize),
    };

    if (query.sortBy && query.sortOrder) {
      params['sort_by'] = query.sortBy;
      params['sort_order'] = query.sortOrder;
    }

    if (query.q) {
      params['q'] = query.q.trim();
    }

    if (query.jdId) {
      params['jd_id'] = query.jdId;
    }

    if (query.skills && query.skills.length > 0) {
      params['skills'] = query.skills.join(',');
    }

    if (query.experienceMin !== undefined) {
      params['experience_min'] = String(query.experienceMin);
    }

    if (query.experienceMax !== undefined) {
      params['experience_max'] = String(query.experienceMax);
    }

    if (query.location) {
      params['location'] = query.location.trim();
    }

    if (query.preferredLocation) {
      params['preferred_location'] = query.preferredLocation.trim();
    }

    if (query.noticePeriodMax !== undefined) {
      params['notice_period_max'] = String(query.noticePeriodMax);
    }

    if (query.status) {
      params['status'] = query.status;
    }

    if (query.degree) {
      params['degree'] = query.degree;
    }

    if (query.certification) {
      params['certification'] = query.certification;
    }

    if (query.resumeUpdatedSince !== undefined) {
      params['resume_updated_since'] = String(query.resumeUpdatedSince);
    }

    if (query.source) {
      params['source'] = query.source;
    }

    if (query.relevantExperience !== undefined) {
      params['relevant_experience'] = String(query.relevantExperience);
    }

    if (query.currentCtc !== undefined) {
      params['current_ctc'] = String(query.currentCtc);
    }

    if (query.expectedCtc !== undefined) {
      params['expected_ctc'] = String(query.expectedCtc);
    }

    if (query.previousCompany) {
      params['previous_company'] = query.previousCompany;
    }

    if (query.employmentStatus) {
      params['employment_status'] = query.employmentStatus;
    }

    return this.httpClient.get<CandidateListResponse>(`${this.apiBaseUrl}/candidates`, { params }).pipe(
      tap(() => this.errorSubject.next(null)),
      catchError((error) => {
        this.errorSubject.next(error?.error?.message || 'Unable to load candidates');
        return of({
          items: [],
          page: query.page,
          page_size: query.pageSize,
          total_items: 0,
          total_pages: 1,
          q: query.q?.trim() || null,
          sort_by: query.sortBy || '',
          sort_order: query.sortOrder || 'asc',
        });
      }),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  loadCandidateDetails(candidateId: string): Observable<CandidateDetailResponse | null> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    return this.httpClient.get<CandidateDetailResponse>(`${this.apiBaseUrl}/candidates/${candidateId}`).pipe(
      tap(() => this.errorSubject.next(null)),
      catchError((error) => {
        this.errorSubject.next(error?.error?.message || 'Unable to load candidate profile');
        return of(null);
      }),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  deleteCandidate(candidateId: string): Observable<void> {
    this.errorSubject.next(null);

    return this.httpClient.delete<void>(`${this.apiBaseUrl}/candidates/${candidateId}`).pipe(
      tap(() => this.errorSubject.next(null)),
      catchError((error) => {
        this.errorSubject.next(error?.error?.message || 'Unable to delete candidate');
        return of(void 0);
      })
    );
  }

  deleteCandidatesBatch(candidateIds: string[]): Observable<{ deleted_count: number; message: string }> {
    this.errorSubject.next(null);

    return this.httpClient
      .post<{ deleted_count: number; message: string }>(`${this.apiBaseUrl}/candidates/batch/delete`, {
        candidate_ids: candidateIds,
      })
      .pipe(
        tap(() => this.errorSubject.next(null)),
        catchError((error) => {
          this.errorSubject.next(error?.error?.message || 'Unable to delete candidates');
          return of({ deleted_count: 0, message: 'Error deleting candidates' });
        })
      );
  }
}
