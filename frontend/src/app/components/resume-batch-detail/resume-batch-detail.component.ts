import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ReviewBatchDetail, CandidateReview } from '../../models/resume-enrichment.model';
import { ResumeEnrichmentService } from '../../services/resume-enrichment.service';

@Component({
  selector: 'app-resume-batch-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './resume-batch-detail.component.html',
  styleUrls: ['./resume-batch-detail.component.scss'],
})
export class ResumeBatchDetailComponent implements OnInit, OnDestroy {
  batch: ReviewBatchDetail | null = null;
  loading = false;
  error: string | null = null;
  page = 1;
  pageSize = 20;
  total = 0;
  batchId: string | null = null;

  private destroy$ = new Subject<void>();

  // Expose Math for template usage
  Math = Math;

  constructor(
    private resumeEnrichmentService: ResumeEnrichmentService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.route.paramMap
      .pipe(takeUntil(this.destroy$))
      .subscribe((params) => {
        this.batchId = params.get('batchId');
        if (this.batchId) {
          this.loadBatchDetail();
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load batch details from backend.
   */
  loadBatchDetail(): void {
    if (!this.batchId) return;

    this.loading = true;
    this.error = null;

    this.resumeEnrichmentService
      .getReviewBatch(this.batchId, this.page, this.pageSize)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (batch) => {
          this.batch = batch;
          this.total = batch.candidates.length;
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading batch detail:', error);
          this.error = 'Failed to load batch details. Please try again.';
          this.loading = false;
        },
      });
  }

  /**
   * Navigate to candidate review.
   */
  reviewCandidate(candidateReviewId: string): void {
    this.router.navigate(['/resume-enrichment/candidates', candidateReviewId]);
  }

  /**
   * Go back to batch list.
   */
  goBack(): void {
    this.router.navigate(['/resume-enrichment/batches']);
  }

  /**
   * Get status badge CSS class.
   */
  getStatusClass(status: string): string {
    return `status-${status.toLowerCase()}`;
  }

  /**
   * Get approval status color.
   */
  getApprovalStatusClass(status: string): string {
    return `approval-${status.toLowerCase()}`;
  }

  /**
   * Get progress percentage.
   */
  getProgressPercentage(): number {
    if (!this.batch || this.batch.total_candidates === 0) return 0;
    return Math.round((this.batch.processed_candidates / this.batch.total_candidates) * 100);
  }

  /**
   * Get pending count.
   */
  getPendingCount(): number {
    if (!this.batch) return 0;
    return this.batch.candidates.filter((c) => c.approval_status === 'PENDING').length;
  }

  /**
   * Get approved count.
   */
  getApprovedCount(): number {
    if (!this.batch) return 0;
    return this.batch.candidates.filter((c) => c.approval_status === 'APPROVED').length;
  }

  /**
   * Get rejected count.
   */
  getRejectedCount(): number {
    if (!this.batch) return 0;
    return this.batch.candidates.filter((c) => c.approval_status === 'REJECTED').length;
  }

  /**
   * Get pending changes count for a candidate.
   */
  getPendingChangesCount(candidate: CandidateReview): number {
    return candidate.proposed_changes.filter((c) => c.change_status === 'PENDING').length;
  }

  /**
   * Go to previous page.
   */
  previousPage(): void {
    if (this.page > 1) {
      this.page--;
      this.loadBatchDetail();
    }
  }

  /**
   * Go to next page.
   */
  nextPage(): void {
    if (this.page * this.pageSize < this.total) {
      this.page++;
      this.loadBatchDetail();
    }
  }

  /**
   * Check if previous button is disabled.
   */
  isPreviousDisabled(): boolean {
    return this.page <= 1 || this.loading;
  }

  /**
   * Check if next button is disabled.
   */
  isNextDisabled(): boolean {
    return this.page * this.pageSize >= this.total || this.loading;
  }

  /**
   * Delete the entire batch with confirmation.
   */
  deleteBatch(): void {
    if (!this.batch) return;

    const confirmDelete = window.confirm(
      `Are you sure you want to delete batch "${this.batch.batch_number}"? ` +
      'This will delete all candidate reviews and proposed changes. This action cannot be undone.'
    );

    if (!confirmDelete) return;

    this.loading = true;
    this.error = null;

    this.resumeEnrichmentService
      .deleteBatch(this.batch.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.loading = false;
          // Navigate back to batch list after successful deletion
          this.router.navigate(['/resume-enrichment/batches']);
        },
        error: (error) => {
          console.error('Error deleting batch:', error);
          this.error = 'Failed to delete batch. Please try again.';
          this.loading = false;
        },
      });
  }
}
