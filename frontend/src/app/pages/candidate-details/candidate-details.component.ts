import { CommonModule } from '@angular/common';
import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../../services/auth.service';

import { CandidateDetailResponse } from '../../models/candidate.models';
import { ZohoIntegrationStatus } from '../../models/integration.models';
import { CandidateService } from '../../services/candidate.service';
import { IntegrationService } from '../../services/integration.service';
import { sanitizeCandidateName, sanitizeDisplayText, sanitizeEmailAddress } from '../../utils/display-format';

@Component({
  selector: 'app-candidate-details',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './candidate-details.component.html',
  styleUrl: './candidate-details.component.css',
})
export class CandidateDetailsComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  candidate: CandidateDetailResponse | null = null;
  zohoStatus: ZohoIntegrationStatus | null = null;
  loading = true;
  errorMessage: string | null = null;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly candidateService: CandidateService,
    private readonly integrationService: IntegrationService,
    private readonly authService: AuthService,
    private readonly router: Router
  ) {
    this.integrationService
      .pollZohoStatus()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((status) => {
        this.zohoStatus = status;
      });

    this.candidateService.error$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((message) => {
      this.errorMessage = message;
    });
  }

  ngOnInit(): void {
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const candidateId = params.get('id');
      if (!candidateId) {
        this.loading = false;
        this.candidate = null;
        this.errorMessage = 'Candidate identifier is missing.';
        return;
      }

      this.loading = true;
      this.candidateService
        .loadCandidateDetails(candidateId)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe((candidate) => {
          this.candidate = candidate;
          this.loading = false;
        });
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

  get isConnected(): boolean {
    return this.zohoStatus?.connection_state === 'connected';
  }

  statusLabel(status: string): string {
    return status.replaceAll('_', ' ');
  }

  noticePeriodLabel(value: number | null): string {
    if (value === null) {
      return '—';
    }

    return `${value} Days`;
  }

  experienceLabel(value: number | null): string {
    if (value === null) {
      return '—';
    }

    return `${value} Years`;
  }

  ctcLabel(value: number | null): string {
    if (value === null) {
      return '—';
    }

    return `₹${value} LPA`;
  }

  matchLabel(): string {
    const percentage = this.candidate?.match_context.match_percentage;
    if (percentage === null || percentage === undefined) {
      return 'N/A Match';
    }

    return `${Math.round(percentage)}% Match`;
  }

  safeName(value: string | null | undefined): string {
    return sanitizeCandidateName(value);
  }

  safeText(value: string | null | undefined): string {
    return sanitizeDisplayText(value);
  }

  safeEmail(value: string | null | undefined): string {
    return sanitizeEmailAddress(value);
  }
}
