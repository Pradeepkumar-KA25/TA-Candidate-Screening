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

  // Accordion state management
  expandedSections: Set<string> = new Set();

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
          console.log('=== CANDIDATE LOADED ===');
          console.log('Candidate:', candidate);
          if (candidate) {
            console.log('Full Name:', candidate.full_name);
            console.log('Has extended_fields property?', 'extended_fields' in candidate);
            console.log('Extended Fields:', candidate.extended_fields);
            if (candidate.extended_fields) {
              console.log('personal_contact:', candidate.extended_fields.personal_contact);
              console.log('employment:', candidate.extended_fields.employment);
              console.log('interview_process:', candidate.extended_fields.interview_process);
              console.log('candidate_lifecycle:', candidate.extended_fields.candidate_lifecycle);
              console.log('salary_benefits:', candidate.extended_fields.salary_benefits);
              console.log('referral_vendor_sourcing:', candidate.extended_fields.referral_vendor_sourcing);
              
              // Check hasExtendedFields result
              const hasExt = this.hasExtendedFields();
              console.log('hasExtendedFields() returns:', hasExt);
            }
          }
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

  deleteCandidate(): void {
    if (!this.candidate) return;
    
    const confirmed = confirm(`Are you sure you want to delete "${this.candidate.full_name}"? This action cannot be undone.`);
    if (!confirmed) return;

    this.loading = true;
    this.candidateService
      .deleteCandidate(this.candidate.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.router.navigate(['/candidates']);
      });
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

  toggleSection(sectionName: string): void {
    if (this.expandedSections.has(sectionName)) {
      this.expandedSections.delete(sectionName);
    } else {
      this.expandedSections.add(sectionName);
    }
  }

  isSectionExpanded(sectionName: string): boolean {
    return this.expandedSections.has(sectionName);
  }

  hasExtendedFields(): boolean {
    console.log('DEBUG hasExtendedFields called');
    console.log('DEBUG candidate:', this.candidate);
    console.log('DEBUG extended_fields:', this.candidate?.extended_fields);
    
    if (!this.candidate?.extended_fields) {
      console.log('DEBUG: No extended_fields property');
      return false;
    }
    const ext = this.candidate.extended_fields;
    console.log('DEBUG: Extended fields exists, checking keys');
    console.log('DEBUG: personal_contact keys:', Object.keys(ext.personal_contact || {}));
    console.log('DEBUG: employment keys:', Object.keys(ext.employment || {}));
    console.log('DEBUG: interview_process keys:', Object.keys(ext.interview_process || {}));
    console.log('DEBUG: candidate_lifecycle keys:', Object.keys(ext.candidate_lifecycle || {}));
    
    return Object.keys(ext.personal_contact || {}).length > 0 ||
           Object.keys(ext.employment || {}).length > 0 ||
           Object.keys(ext.interview_process || {}).length > 0 ||
           Object.keys(ext.candidate_lifecycle || {}).length > 0 ||
           Object.keys(ext.salary_benefits || {}).length > 0 ||
           Object.keys(ext.referral_vendor_sourcing || {}).length > 0;
  }

  hasPersonalContact(): boolean {
    const data = this.candidate?.extended_fields?.personal_contact;
    return !!(data && Object.keys(data).length > 0);
  }

  hasEmployment(): boolean {
    const data = this.candidate?.extended_fields?.employment;
    return !!(data && Object.keys(data).length > 0);
  }

  hasInterviewProcess(): boolean {
    const data = this.candidate?.extended_fields?.interview_process;
    return !!(data && Object.keys(data).length > 0);
  }

  hasCandidateLifecycle(): boolean {
    const data = this.candidate?.extended_fields?.candidate_lifecycle;
    return !!(data && Object.keys(data).length > 0);
  }

  hasSalaryBenefits(): boolean {
    const data = this.candidate?.extended_fields?.salary_benefits;
    return !!(data && Object.keys(data).length > 0);
  }

  hasReferralVendor(): boolean {
    const data = this.candidate?.extended_fields?.referral_vendor_sourcing;
    return !!(data && Object.keys(data).length > 0);
  }
}

