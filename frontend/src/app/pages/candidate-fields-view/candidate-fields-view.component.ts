import { Component, OnInit, inject, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

import { CandidateDetailResponse } from '../../models/candidate.models';
import { CandidateService } from '../../services/candidate.service';
import { CandidateFieldsService, FieldGroup } from '../../services/candidate-fields.service';
import { CandidateFieldSectionComponent } from '../../components/candidate-field-section/candidate-field-section.component';
import { sanitizeCandidateName, sanitizeDisplayText, sanitizeEmailAddress } from '../../utils/display-format';

@Component({
  selector: 'app-candidate-fields-view',
  standalone: true,
  imports: [
    CommonModule,
    CandidateFieldSectionComponent
  ],
  templateUrl: './candidate-fields-view.component.html',
  styleUrl: './candidate-fields-view.component.css'
})
export class CandidateFieldsViewComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly candidateService = inject(CandidateService);
  private readonly fieldsService = inject(CandidateFieldsService);
  private readonly sanitizer = inject(DomSanitizer);

  candidate: CandidateDetailResponse | null = null;
  fieldGroups: FieldGroup[] = [];
  loading = true;
  errorMessage: string | null = null;
  showResumeViewer = false;
  resumeUrl: SafeResourceUrl | null = null;

  ngOnInit(): void {
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const candidateId = params.get('id');
      if (!candidateId) {
        this.loading = false;
        this.errorMessage = 'Candidate identifier is missing.';
        return;
      }

      this.loading = true;
      this.candidateService
        .loadCandidateDetails(candidateId)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe((candidate) => {
          if (candidate) {
            this.candidate = candidate;
            
            // Process raw payload to extract and group all fields
            if (candidate.extended_fields) {
              this.fieldGroups = this.fieldsService.groupCandidateFields(candidate.extended_fields);
            }
          }
          this.loading = false;
        });
    });
  }

  goBack(): void {
    window.history.back();
  }

  deleteCandidate(): void {
    if (!this.candidate) return;
    
    const confirmed = confirm(
      `Are you sure you want to delete "${this.candidate.full_name}"? This action cannot be undone.`
    );
    if (!confirmed) return;

    this.loading = true;
    this.candidateService
      .deleteCandidate(this.candidate.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.router.navigate(['/candidates']);
      });
  }

  downloadResume(): void {
    if (!this.candidate?.resume_url) {
      alert('No resume available for this candidate.');
      return;
    }

    // Show resume in embedded viewer
    const resumeUrl = `/api/v1/candidates/${this.candidate.id}/resume`;
    this.resumeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(resumeUrl);
    this.showResumeViewer = true;
  }

  closeResumeViewer(): void {
    this.showResumeViewer = false;
    this.resumeUrl = null;
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

  onFieldGroupToggled(group: FieldGroup): void {
    // Handle any side effects if needed
    console.log(`Toggled field group: ${group.category}, expanded: ${group.expanded}`);
  }

  downloadResumeFile(): void {
    if (!this.candidate?.resume_url) return;
    const resumeUrl = `/api/v1/candidates/${this.candidate.id}/resume`;
    const link = document.createElement('a');
    link.href = resumeUrl;
    link.download = this.candidate.resume_file_name || 'resume';
    link.click();
  }
}

