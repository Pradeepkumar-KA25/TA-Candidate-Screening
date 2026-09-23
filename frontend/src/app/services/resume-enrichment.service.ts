import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  CandidateReview,
  CandidateReviewListResponse,
  ProposedFieldChange,
  ReviewBatch,
  ReviewBatchDetail,
  ReviewBatchListResponse,
} from '../models/resume-enrichment.model';
import { ApiConfigService } from '../config/api.config';

@Injectable({
  providedIn: 'root',
})
export class ResumeEnrichmentService {
  private apiBaseUrl: string;

  constructor(
    private http: HttpClient,
    private apiConfig: ApiConfigService
  ) {
    this.apiBaseUrl = this.apiConfig.getApiBaseUrl();
  }

  /**
   * Create a new review batch and process candidates.
   * @param batchSize Optional batch size (defaults to config value)
   * @returns Observable of created batch
   */
  createBatch(batchSize?: number): Observable<ReviewBatch> {
    return this.http.post<ReviewBatch>(`${this.apiBaseUrl}/resume-enrichment/batches`, {
      batch_size: batchSize || null,
    });
  }

  /**
   * Get paginated list of review batches.
   * @param page Page number (1-indexed)
   * @param pageSize Results per page
   * @returns Observable of batch list response
   */
  listBatches(page: number = 1, pageSize: number = 10): Observable<ReviewBatchListResponse> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    return this.http.get<ReviewBatchListResponse>(`${this.apiBaseUrl}/resume-enrichment/batches`, { params });
  }

  /**
   * Get a specific review batch with candidate details.
   * @param batchId UUID of the batch
   * @param page Page number for candidates (1-indexed)
   * @param pageSize Results per page
   * @returns Observable of batch detail with candidates
   */
  getReviewBatch(batchId: string, page: number = 1, pageSize: number = 20): Observable<ReviewBatchDetail> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());

    return this.http.get<ReviewBatchDetail>(`${this.apiBaseUrl}/resume-enrichment/batches/${batchId}`, { params });
  }

  /**
   * Get a candidate review with all proposed field changes.
   * @param candidateReviewId UUID of the candidate review
   * @returns Observable of candidate review with proposed changes
   */
  getCandidateReview(candidateReviewId: string): Observable<CandidateReview> {
    return this.http.get<CandidateReview>(`${this.apiBaseUrl}/resume-enrichment/candidates/${candidateReviewId}`);
  }

  /**
   * Approve proposed changes for a candidate.
   * @param candidateReviewId UUID of the candidate review
   * @param fieldIds Specific field IDs to approve (undefined = approve all)
   * @param notes Optional approval notes
   * @returns Observable of success response
   */
  approveCandidateChanges(
    candidateReviewId: string,
    fieldIds?: string[],
    notes?: string
  ): Observable<{ message: string }> {
    const body = {
      field_ids: fieldIds || null,
      notes: notes || null,
    };

    return this.http.patch<{ message: string }>(
      `${this.apiBaseUrl}/resume-enrichment/candidates/${candidateReviewId}/approve`,
      body
    );
  }

  /**
   * Reject proposed changes for a candidate.
   * @param candidateReviewId UUID of the candidate review
   * @param fieldIds Specific field IDs to reject (undefined = reject all)
   * @param notes Optional rejection notes
   * @returns Observable of success response
   */
  rejectCandidateChanges(
    candidateReviewId: string,
    fieldIds?: string[],
    notes?: string
  ): Observable<{ message: string }> {
    const body = {
      field_ids: fieldIds || null,
      notes: notes || null,
    };

    return this.http.patch<{ message: string }>(
      `${this.apiBaseUrl}/resume-enrichment/candidates/${candidateReviewId}/reject`,
      body
    );
  }

  /**
   * Delete a review batch and all related records.
   * @param batchId UUID of the batch to delete
   * @returns Observable of delete response
   */
  deleteBatch(batchId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiBaseUrl}/resume-enrichment/batches/${batchId}`);
  }
}
