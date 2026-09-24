import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ReviewBatch } from '../../models/resume-enrichment.model';
import { ResumeEnrichmentService } from '../../services/resume-enrichment.service';

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
  showBatchSizeDialog = false;
  batchSize = 20;
  error: string | null = null;
  page = 1;
  pageSize = 10;
  total = 0;

  private destroy$ = new Subject<void>();

  constructor(
    private resumeEnrichmentService: ResumeEnrichmentService,
    private router: Router
  ) {}

  // Expose Math for template usage
  Math = Math;

  ngOnInit(): void {
    this.loadBatches();
  }

  ngOnDestroy(): void {
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
        },
        error: (error) => {
          console.error('Error loading batches:', error);
          this.error = 'Failed to load review batches. Please try again.';
          this.loading = false;
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
    this.error = null;
  }

  cancelBatchCreation(): void {
    if (!this.creating) {
      this.showBatchSizeDialog = false;
    }
  }

  createBatch(): void {
    if (this.creating || this.batchSize < 1 || this.batchSize > 1000) return;

    this.creating = true;
    this.showBatchSizeDialog = false;
    this.error = null;

    this.resumeEnrichmentService
      .createBatch(this.batchSize)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (batch) => {
          this.creating = false;
          // Navigate to batch detail
          this.router.navigate(['/resume-enrichment/batches', batch.id]);
        },
        error: (error) => {
          console.error('Error creating batch:', error);
          this.error = 'Failed to create review batch. Please try again.';
          this.creating = false;
        },
      });
  }

  /**
   * Navigate to batch detail view.
   */
  viewBatch(batchId: string): void {
    this.router.navigate(['/resume-enrichment/batches', batchId]);
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
