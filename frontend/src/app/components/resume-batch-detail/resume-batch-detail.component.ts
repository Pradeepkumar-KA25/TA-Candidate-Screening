import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ReviewBatchDetail, CandidateReview } from '../../models/resume-enrichment.model';
import { ResumeEnrichmentService } from '../../services/resume-enrichment.service';
import { NotificationService } from '../../services/notification.service';

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
  showDeleteConfirmation = false;
  page = 1;
  pageSize = 20;
  total = 0;
  batchId: string | null = null;
  batchWriteBackLoading = false;

  private destroy$ = new Subject<void>();

  // Expose Math for template usage
  Math = Math;

  constructor(
    private resumeEnrichmentService: ResumeEnrichmentService,
    private route: ActivatedRoute,
    private router: Router,
    private notificationService: NotificationService,
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
          this.total = batch.candidate_total;
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading batch detail:', error);
          this.error = 'Failed to load batch details. Please try again.';
          this.loading = false;
          this.notificationService.error(this.error, 'Resume enrichment');
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

  getSendableCount(): number {
    if (!this.batch) return 0;
    return this.batch.candidates.filter((candidate) =>
      candidate.proposed_changes.some((change) => change.change_status === 'APPROVED')
    ).length;
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

    this.loading = true;
    this.showDeleteConfirmation = false;
    this.error = null;

    this.resumeEnrichmentService
      .deleteBatch(this.batch.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.loading = false;
          this.notificationService.success('The review batch was deleted.', 'Resume enrichment');
          // Navigate back to batch list after successful deletion
          this.router.navigate(['/resume-enrichment/batches']);
        },
        error: (error) => {
          console.error('Error deleting batch:', error);
          this.error = 'Failed to delete batch. Please try again.';
          this.loading = false;
          this.notificationService.error(this.error, 'Resume enrichment');
        },
      });
  }

  cancelDelete(): void {
    if (!this.loading) {
      this.showDeleteConfirmation = false;
    }
  }

  sendApprovedBatch(): void {
    if (!this.batch || this.batchWriteBackLoading) return;

    this.batchWriteBackLoading = true;
    this.resumeEnrichmentService
      .sendApprovedBatch(this.batch.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.batchWriteBackLoading = false;
          if (response['sent_to_zoho'] === false) {
            this.notificationService.info('Zoho write-back is disabled. No candidate data was sent.', 'Batch write-back disabled');
          } else {
            this.notificationService.success('Approved batch changes were processed.', 'Batch write-back');
          }
        },
        error: (error) => {
          console.error('Error processing approved batch:', error);
          this.batchWriteBackLoading = false;
          this.notificationService.error('Failed to process approved batch changes.', 'Batch write-back');
        },
      });
  }
}
