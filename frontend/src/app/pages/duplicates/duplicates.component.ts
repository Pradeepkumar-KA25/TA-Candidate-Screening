import { CommonModule } from '@angular/common';
import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../services/auth.service';

import { DuplicateGroupItem, DuplicatePairItem, DuplicateSummary } from '../../models/duplicate.models';
import { DuplicateService } from '../../services/duplicate.service';
import { sanitizeCandidateName, sanitizeDisplayText } from '../../utils/display-format';

@Component({
  selector: 'app-duplicates',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './duplicates.component.html',
  styleUrl: './duplicates.component.css',
})
export class DuplicatesComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  groups: DuplicateGroupItem[] = [];
  loading = false;
  error: string | null = null;
  reviewingIds = new Set<string>();
  summary: DuplicateSummary = {
    job_descriptions_reviewed: 0,
    possible_duplicates: 0,
    no_duplicate_signal: 0,
    unassigned_duplicates: 0,
  };

  constructor(
    private readonly duplicateService: DuplicateService,
    private readonly authService: AuthService,
    private readonly router: Router
  ) {}

  ngOnInit(): void {
    this.duplicateService.loading$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((value) => {
        this.loading = value;
      });

    this.duplicateService.error$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((value) => {
        this.error = value;
      });

    this.duplicateService
      .listGroupedDuplicates()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((response) => {
        if (!response) {
          return;
        }
        this.summary = response.summary;
        this.groups = response.groups;
      });
  }

  onLogout(): void {
    this.authService.logoutFromServer().pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.router.navigate(['/login']);
    });
  }

  goBack(): void {
    window.history.back();
  }

  safeName(value: string | null | undefined): string {
    return sanitizeCandidateName(value);
  }

  safeText(value: string | null | undefined): string {
    return sanitizeDisplayText(value);
  }

  formatJdLabel(group: DuplicateGroupItem): string {
    if (group.jd_code) {
      return group.jd_code;
    }
    return 'NO-JD';
  }

  formatConfidence(confidence: number): string {
    return `${Math.round(confidence * 100)}%`;
  }

  formatMatchBasis(matchBasis: string): string {
    const normalized = (matchBasis || '').trim();
    if (!normalized) {
      return 'Not specified';
    }

    return normalized
      .split('_')
      .map((item) => item.charAt(0).toUpperCase() + item.slice(1).toLowerCase())
      .join(' ');
  }

  statusLabel(item: DuplicatePairItem): string {
    return item.status === 'reviewed' ? 'Reviewed' : 'Pending Review';
  }

  isReviewed(item: DuplicatePairItem): boolean {
    return item.status === 'reviewed';
  }

  markAsReviewed(item: DuplicatePairItem): void {
    if (this.isReviewed(item) || this.reviewingIds.has(item.id)) {
      return;
    }

    this.reviewingIds.add(item.id);
    this.duplicateService
      .markReviewed(item.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((updated) => {
        this.reviewingIds.delete(item.id);
        if (!updated) {
          return;
        }

        for (const group of this.groups) {
          const target = group.items.find((entry) => entry.id === updated.id);
          if (!target) {
            continue;
          }
          target.status = updated.status;
          target.reviewed_at = updated.reviewed_at ?? null;
          target.reviewed_by = updated.reviewed_by ?? null;
          break;
        }
      });
  }
}
