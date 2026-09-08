import { CommonModule } from '@angular/common';
import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { JobDescriptionListItem } from '../../models/job-description.models';
import { ZohoIntegrationStatus } from '../../models/integration.models';
import { AuthService } from '../../services/auth.service';
import { IntegrationService } from '../../services/integration.service';
import { JobDescriptionService } from '../../services/job-description.service';
import { ShortlistListItem, ShortlistService } from '../../services/shortlist.service';
import { sanitizeCandidateName, sanitizeDisplayText, summarizeSkills } from '../../utils/display-format';

@Component({
  selector: 'app-shortlists',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './shortlists.component.html',
  styleUrl: './shortlists.component.css',
})
export class ShortlistsComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  shortlists: ShortlistListItem[] = [];
  jobDescriptions: JobDescriptionListItem[] = [];
  selectedJdId = '';
  loading = false;
  downloadingShortlistId: string | null = null;
  removingCandidateKey: string | null = null;
  errorMessage: string | null = null;
  zohoStatus: ZohoIntegrationStatus | null = null;

  constructor(
    private readonly authService: AuthService,
    private readonly integrationService: IntegrationService,
    private readonly jobDescriptionService: JobDescriptionService,
    private readonly shortlistService: ShortlistService,
    private readonly route: ActivatedRoute,
    private readonly router: Router
  ) {
    this.integrationService
      .pollZohoStatus()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((status) => {
        this.zohoStatus = status;
      });
  }

  ngOnInit(): void {
    this.jobDescriptionService
      .listJobDescriptions()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((items) => {
        this.jobDescriptions = items;
      });

    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const jdId = params.get('jd_id') || '';
      this.selectedJdId = jdId;
      this.loadShortlists();
    });
  }

  get isConnected(): boolean {
    return this.zohoStatus?.connection_state === 'connected';
  }

  onLogout(): void {
    this.authService.logoutFromServer().pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.router.navigate(['/login']);
    });
  }

  goBack(): void {
    window.history.back();
  }

  onJdChange(jdId: string): void {
    this.selectedJdId = jdId;
    const queryParams = jdId ? { jd_id: jdId } : {};
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams,
      queryParamsHandling: '',
    });
  }

  async downloadShortlist(shortlistId: string): Promise<void> {
    this.downloadingShortlistId = shortlistId;
    this.errorMessage = null;
    try {
      await this.shortlistService.downloadShortlistAsExcel(shortlistId).toPromise();
    } catch {
      this.errorMessage = 'Unable to download shortlist right now. Please try again.';
    } finally {
      this.downloadingShortlistId = null;
    }
  }

  async removeCandidate(shortlistId: string, candidateId: string): Promise<void> {
    this.errorMessage = null;
    const removeKey = `${shortlistId}:${candidateId}`;
    this.removingCandidateKey = removeKey;

    try {
      await firstValueFrom(this.shortlistService.removeCandidateFromShortlist(shortlistId, candidateId));

      this.shortlists = this.shortlists
        .map((shortlist) => {
          if (shortlist.id !== shortlistId) {
            return shortlist;
          }

          const updatedCandidates = shortlist.candidates.filter((candidate) => candidate.id !== candidateId);
          return {
            ...shortlist,
            candidates: updatedCandidates,
            candidate_count: updatedCandidates.length,
          };
        })
        .filter((shortlist) => shortlist.candidate_count > 0);
    } catch {
      this.errorMessage = 'Unable to remove candidate from shortlist right now. Please try again.';
    } finally {
      this.removingCandidateKey = null;
    }
  }

  isRemovingCandidate(shortlistId: string, candidateId: string): boolean {
    return this.removingCandidateKey === `${shortlistId}:${candidateId}`;
  }

  safeName(value: string | null | undefined): string {
    return sanitizeCandidateName(value);
  }

  safeText(value: string | null | undefined): string {
    return sanitizeDisplayText(value);
  }

  skillsText(skills: string[] | null | undefined): string {
    return summarizeSkills(skills ?? null);
  }

  formatDate(value: string): string {
    return new Date(value).toLocaleString();
  }

  private loadShortlists(): void {
    if (!this.selectedJdId) {
      this.shortlists = [];
      this.loading = false;
      this.errorMessage = null;
      return;
    }

    this.loading = true;
    this.errorMessage = null;

    this.shortlistService
      .listShortlists(this.selectedJdId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (items) => {
          this.shortlists = items;
          this.loading = false;
        },
        error: () => {
          this.shortlists = [];
          this.loading = false;
          this.errorMessage = 'Unable to load shortlists. Please refresh and try again.';
        },
      });
  }
}
