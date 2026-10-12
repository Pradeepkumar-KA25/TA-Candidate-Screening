import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ReviewBatch } from '../../models/resume-enrichment.model';
import { ResumeEnrichmentService } from '../../services/resume-enrichment.service';
import { NotificationService } from '../../services/notification.service';

@Component({
  selector: 'app-resume-batch-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './resume-batch-list.component.html',
  styleUrls: ['./resume-batch-list.component.scss'],
})
export class ResumeBatchListComponent implements OnInit, OnDestroy {
  batches: ReviewBatch[] = [];
  loading = false;
  creating = false;
  exporting = false;
  showBatchSizeDialog = false;
  showLargeBatchWarning = false;
  allowLargeBatchCreation = false;
  batchSize = 20;
  batchSizeError: string | null = null;
  error: string | null = null;
  page = 1;
  pageSize = 10;
  total = 0;

  private destroy$ = new Subject<void>();
  private refreshTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(
    private resumeEnrichmentService: ResumeEnrichmentService,
    private router: Router,
    private notificationService: NotificationService,
  ) {}

  // Expose Math for template usage
  Math = Math;

  ngOnInit(): void {
    this.loadBatches();
  }

  ngOnDestroy(): void {
    if (this.refreshTimer) clearTimeout(this.refreshTimer);
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load review batches from backend.
   */
  loadBatches(): void {
    this.loading = true;
    this.error = null;

    this.resumeEnrichmentService
      .listBatches(this.page, this.pageSize)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.batches = response.batches;
          this.total = response.total;
          this.loading = false;
          this.scheduleRefresh(response.batches);
        },
        error: (error) => {
          console.error('Error loading batches:', error);
          this.error = 'Failed to load review batches. Please try again.';
          this.loading = false;
          this.notificationService.error(this.error, 'Resume enrichment');
        },
      });
  }

  /**
   * Create a new review batch.
   */
  openBatchSizeDialog(): void {
    if (this.creating || this.loading) return;
    this.batchSize = 20;
    this.showBatchSizeDialog = true;
    this.showLargeBatchWarning = false;
    this.allowLargeBatchCreation = false;
    this.batchSizeError = null;
    this.error = null;
  }

  cancelBatchCreation(): void {
    if (!this.creating) {
      this.showBatchSizeDialog = false;
      this.showLargeBatchWarning = false;
      this.allowLargeBatchCreation = false;
      this.batchSizeError = null;
    }
  }

  editBatchSize(): void {
    this.showLargeBatchWarning = false;
    this.allowLargeBatchCreation = false;
    this.batchSizeError = null;
  }

  continueWithLargeBatch(): void {
    this.showLargeBatchWarning = false;
    this.allowLargeBatchCreation = true;
    this.createBatch();
  }

  createBatch(): void {
    if (this.creating) return;
    if (!Number.isInteger(this.batchSize) || this.batchSize < 1 || this.batchSize > 1000) {
      this.batchSizeError = 'Enter a whole number between 1 and 1000 candidates.';
      return;
    }
    if (this.batchSize > 50 && !this.allowLargeBatchCreation) {
      this.showLargeBatchWarning = true;
      return;
    }

    this.creating = true;
    this.showBatchSizeDialog = false;
    this.allowLargeBatchCreation = false;
    this.error = null;

    this.resumeEnrichmentService
      .createBatch(this.batchSize)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (batch) => {
          this.creating = false;
          this.notificationService.success(`Batch ${batch.batch_number} is processing in the background.`, 'Resume enrichment');
          // Navigate to batch detail
          this.router.navigate(['/resume-enrichment/batches', batch.id]);
        },
        error: (error) => {
          console.error('Error creating batch:', error);
          this.error = 'Failed to create review batch. Please try again.';
          this.creating = false;
          this.notificationService.error(this.error, 'Resume enrichment');
        },
      });
  }

  /**
   * Navigate to batch detail view.
   */
  viewBatch(batchId: string): void {
    this.router.navigate(['/resume-enrichment/batches', batchId]);
  }

  exportApprovedChanges(): void {
    if (this.exporting) return;
    this.exporting = true;
    this.error = null;

    this.resumeEnrichmentService
      .downloadApprovedChangesAsExcel()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (count) => {
          this.exporting = false;
          this.notificationService.success(
            `Downloaded ${count} approved field change${count === 1 ? '' : 's'} for Zoho Recruit.`,
            'Resume enrichment',
          );
          this.loadBatches();
        },
        error: (error) => {
          this.exporting = false;
          const detail = typeof error?.error?.detail === 'string' ? error.error.detail : null;
          const message = detail || 'No approved changes are available for export.';
          if (error?.status === 409) {
            this.notificationService.warning(message, 'Nothing to export');
            return;
          }
          this.error = message;
          this.notificationService.error(message, 'Resume enrichment');
        },
      });
  }

  /**
   * Get status badge CSS class.
   */
  getStatusClass(status: string): string {
    return `status-${status.toLowerCase()}`;
  }

  /**
   * Get progress percentage.
   */
  getProgressPercentage(batch: ReviewBatch): number {
    if (batch.total_candidates === 0) return 0;
    return Math.round((batch.processed_candidates / batch.total_candidates) * 100);
  }

  private scheduleRefresh(batches: ReviewBatch[]): void {
    if (this.refreshTimer) clearTimeout(this.refreshTimer);
    if (!batches.some((batch) => batch.status === 'PENDING' || batch.status === 'PROCESSING')) return;
    this.refreshTimer = setTimeout(() => this.loadBatches(), 3000);
  }

  /**
   * Go to previous page.
   */
  previousPage(): void {
    if (this.page > 1) {
      this.page--;
      this.loadBatches();
    }
  }

  /**
   * Go to next page.
   */
  nextPage(): void {
    if (this.page * this.pageSize < this.total) {
      this.page++;
      this.loadBatches();
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
}
