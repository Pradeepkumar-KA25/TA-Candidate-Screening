import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { CandidateReview, ProposedFieldChange } from '../../models/resume-enrichment.model';
import { ResumeEnrichmentService } from '../../services/resume-enrichment.service';

@Component({
  selector: 'app-candidate-review',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './candidate-review.component.html',
  styleUrls: ['./candidate-review.component.scss'],
})
export class CandidateReviewComponent implements OnInit, OnDestroy {
  candidateReview: CandidateReview | null = null;
  loading = false;
  submitting = false;
  error: string | null = null;
  success: string | null = null;
  candidateReviewId: string | null = null;

  // Form state
  approvalNotes = '';
  selectedFieldIds: Set<string> = new Set();
  bulkActionNotes = '';
  selectedAction: 'approve' | 'reject' | null = null;
  showBulkActionForm = false;

  private destroy$ = new Subject<void>();

  // Expose Math for template usage
  Math = Math;

  constructor(
    private resumeEnrichmentService: ResumeEnrichmentService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  /**
   * Format field values for display
   * Handles strings, objects, arrays, and other types
   */
  formatFieldValue(value: unknown): string {
    if (value === null || value === undefined) {
      return '(empty)';
    }

    if (typeof value === 'string') {
      return value;
    }

    if (typeof value === 'object') {
      if (Array.isArray(value)) {
        // Format arrays as comma-separated list
        return value
          .map((item) => {
            if (typeof item === 'string') return item;
            if (typeof item === 'object' && item !== null) return this.formatObjectAsText(item as Record<string, unknown>);
            return String(item);
          })
          .join(', ');
      } else {
        // Format objects as readable text
        return this.formatObjectAsText(value as Record<string, unknown>);
      }
    }

    return String(value);
  }

  /**
   * Convert object to readable text format
   */
  private formatObjectAsText(obj: Record<string, unknown>): string {
    const parts: string[] = [];
    for (const [key, val] of Object.entries(obj)) {
      if (val === null || val === undefined) continue;
      if (Array.isArray(val)) {
        parts.push(`${key}: ${val.join(', ')}`);
      } else if (typeof val === 'object') {
        parts.push(`${key}: ${this.formatObjectAsText(val as Record<string, unknown>)}`);
      } else {
        parts.push(`${key}: ${val}`);
      }
    }
    return parts.join(' | ');
  }

  ngOnInit(): void {
    this.route.paramMap
      .pipe(takeUntil(this.destroy$))
      .subscribe((params) => {
        this.candidateReviewId = params.get('candidateReviewId');
        if (this.candidateReviewId) {
          this.loadCandidateReview();
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load candidate review from backend.
   */
  loadCandidateReview(): void {
    if (!this.candidateReviewId) return;

    this.loading = true;
    this.error = null;

    this.resumeEnrichmentService
      .getCandidateReview(this.candidateReviewId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (candidateReview) => {
          this.candidateReview = candidateReview;
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading candidate review:', error);
          this.error = 'Failed to load candidate review. Please try again.';
          this.loading = false;
        },
      });
  }

  /**
   * Go back to batch detail.
   */
  goBack(): void {
    if (this.candidateReview) {
      this.router.navigate(['/resume-enrichment/batches', this.candidateReview.batch_id]);
    }
  }

  /**
   * Toggle field selection.
   */
  toggleFieldSelection(fieldId: string): void {
    if (this.selectedFieldIds.has(fieldId)) {
      this.selectedFieldIds.delete(fieldId);
    } else {
      this.selectedFieldIds.add(fieldId);
    }
  }

  /**
   * Select all pending fields.
   */
  selectAllPending(): void {
    if (!this.candidateReview) return;

    this.candidateReview.proposed_changes.forEach((change) => {
      if (change.change_status === 'PENDING') {
        this.selectedFieldIds.add(change.id);
      }
    });
  }

  /**
   * Deselect all fields.
   */
  deselectAll(): void {
    this.selectedFieldIds.clear();
  }

  /**
   * Get pending changes only.
   */
  getPendingChanges(): ProposedFieldChange[] {
    if (!this.candidateReview) return [];
    return this.candidateReview.proposed_changes.filter((c) => c.change_status === 'PENDING');
  }

  /**
   * Get approved changes.
   */
  getApprovedChanges(): ProposedFieldChange[] {
    if (!this.candidateReview) return [];
    return this.candidateReview.proposed_changes.filter((c) => c.change_status === 'APPROVED');
  }

  /**
   * Get rejected changes.
   */
  getRejectedChanges(): ProposedFieldChange[] {
    if (!this.candidateReview) return [];
    return this.candidateReview.proposed_changes.filter((c) => c.change_status === 'REJECTED');
  }

  /**
   * Show bulk action form.
   */
  showBulkAction(action: 'approve' | 'reject'): void {
    if (this.selectedFieldIds.size === 0) {
      this.error = 'Please select at least one field';
      return;
    }

    this.selectedAction = action;
    this.showBulkActionForm = true;
    this.error = null;
  }

  /**
   * Cancel bulk action.
   */
  cancelBulkAction(): void {
    this.showBulkActionForm = false;
    this.selectedAction = null;
    this.bulkActionNotes = '';
  }

  /**
   * Submit bulk action (approve or reject).
   */
  submitBulkAction(): void {
    if (!this.candidateReviewId) return;

    if (this.selectedFieldIds.size === 0) {
      this.error = 'Please select at least one field';
      return;
    }

    if (!this.selectedAction) {
      this.error = 'No action selected';
      return;
    }

    this.submitting = true;
    this.error = null;
    this.success = null;

    const fieldIds = Array.from(this.selectedFieldIds);
    const notes = this.bulkActionNotes || undefined;

    const action$ =
      this.selectedAction === 'approve'
        ? this.resumeEnrichmentService.approveCandidateChanges(
            this.candidateReviewId,
            fieldIds,
            notes
          )
        : this.resumeEnrichmentService.rejectCandidateChanges(
            this.candidateReviewId,
            fieldIds,
            notes
          );

    action$
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.success = response.message;
          this.submitting = false;
          this.cancelBulkAction();
          this.selectedFieldIds.clear();

          // Reload candidate review
          setTimeout(() => this.loadCandidateReview(), 500);
        },
        error: (error) => {
          console.error('Error submitting action:', error);
          this.error = `Failed to ${this.selectedAction} changes. Please try again.`;
          this.submitting = false;
        },
      });
  }

  /**
   * Approve all pending changes at once.
   */
  approveAll(): void {
    if (!this.candidateReviewId) return;

    if (this.getPendingChanges().length === 0) {
      this.error = 'No pending changes to approve';
      return;
    }

    this.submitting = true;
    this.error = null;
    this.success = null;

    this.resumeEnrichmentService
      .approveCandidateChanges(this.candidateReviewId, undefined, this.approvalNotes || undefined)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.success = response.message;
          this.submitting = false;
          this.approvalNotes = '';

          // Reload candidate review
          setTimeout(() => this.loadCandidateReview(), 500);
        },
        error: (error) => {
          console.error('Error approving all:', error);
          this.error = 'Failed to approve all changes. Please try again.';
          this.submitting = false;
        },
      });
  }

  /**
   * Reject all pending changes at once.
   */
  rejectAll(): void {
    if (!this.candidateReviewId) return;

    if (this.getPendingChanges().length === 0) {
      this.error = 'No pending changes to reject';
      return;
    }

    this.submitting = true;
    this.error = null;
    this.success = null;

    this.resumeEnrichmentService
      .rejectCandidateChanges(this.candidateReviewId, undefined, this.approvalNotes || undefined)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.success = response.message;
          this.submitting = false;
          this.approvalNotes = '';

          // Reload candidate review
          setTimeout(() => this.loadCandidateReview(), 500);
        },
        error: (error) => {
          console.error('Error rejecting all:', error);
          this.error = 'Failed to reject all changes. Please try again.';
          this.submitting = false;
        },
      });
  }

  /**
   * Get field change status badge class.
   */
  getChangeStatusClass(status: string): string {
    return `badge-${status.toLowerCase()}`;
  }

  /**
   * Check if field is selected.
   */
  isFieldSelected(fieldId: string): boolean {
    return this.selectedFieldIds.has(fieldId);
  }
}
