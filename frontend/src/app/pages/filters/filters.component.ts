import { CommonModule } from '@angular/common';
import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { take } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { CreateJobDescriptionRequest, JobDescriptionListItem } from '../../models/job-description.models';
import { SaveFilterRequest } from '../../models/saved-filter.models';
import { AuthService } from '../../services/auth.service';
import { JobDescriptionService } from '../../services/job-description.service';
import { SavedFilterService } from '../../services/saved-filter.service';

@Component({
  selector: 'app-filters',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './filters.component.html',
  styleUrl: './filters.component.css',
})
export class FiltersComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  readonly createJdForm = new FormGroup({
    jdCode: new FormControl<string>('', { nonNullable: true }),
    title: new FormControl<string>('', { nonNullable: true }),
    requiredSkills: new FormControl<string>('', { nonNullable: true }),
  });

  readonly filterForm = new FormGroup({
    jdId: new FormControl<string>('any', { nonNullable: true }),
    skills: new FormControl<string>('', { nonNullable: true }),
    experienceMin: new FormControl<string>('', { nonNullable: true }),
    experienceMax: new FormControl<string>('', { nonNullable: true }),
    location: new FormControl<string>('', { nonNullable: true }),
    preferredLocation: new FormControl<string>('', { nonNullable: true }),
    noticePeriodMax: new FormControl<string>('', { nonNullable: true }),
    status: new FormControl<string>('any', { nonNullable: true }),
    degree: new FormControl<string>('', { nonNullable: true }),
    certification: new FormControl<string>('', { nonNullable: true }),
    resumeUpdatedSince: new FormControl<string>('', { nonNullable: true }),
    source: new FormControl<string>('', { nonNullable: true }),
    relevantExperience: new FormControl<string>('', { nonNullable: true }),
    currentCtc: new FormControl<string>('', { nonNullable: true }),
    expectedCtc: new FormControl<string>('', { nonNullable: true }),
    previousCompany: new FormControl<string>('', { nonNullable: true }),
    employmentStatus: new FormControl<string>('', { nonNullable: true }),
  });

  jobDescriptions: JobDescriptionListItem[] = [];
  isSaveModalOpen = false;
  saveNameControl = new FormControl<string>('', { nonNullable: true });
  saveNameValidationMessage: string | null = null;
  saveApiMessage: string | null = null;
  duplicateWarning: string | null = null;
  applyValidationMessage: string | null = null;
  jdCreateValidationMessage: string | null = null;
  jdCreateApiMessage: string | null = null;
  jdCreateSuccessMessage: string | null = null;
  jdCreateInProgress = false;
  savingInProgress = false;

  constructor(
    private readonly router: Router,
    private readonly authService: AuthService,
    private readonly jobDescriptionService: JobDescriptionService,
    private readonly savedFilterService: SavedFilterService
  ) {}

  onLogout(): void {
    this.authService.logoutFromServer().pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.router.navigate(['/login']);
    });
  }

  goBack(): void {
    window.history.back();
  }

  ngOnInit(): void {
    this.loadJobDescriptions();

    this.savedFilterService.loading$.subscribe((loading) => {
      this.savingInProgress = loading;
    });
  }

  createJobDescription(): void {
    const jdCode = this.asInputText(this.createJdForm.controls.jdCode.value).trim();
    const title = this.asInputText(this.createJdForm.controls.title.value).trim();
    const requiredSkills = this.asInputText(this.createJdForm.controls.requiredSkills.value)
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item.length > 0);

    if (!jdCode || !title) {
      this.jdCreateValidationMessage = 'JD Code and Title are required.';
      this.jdCreateApiMessage = null;
      this.jdCreateSuccessMessage = null;
      return;
    }

    this.jdCreateValidationMessage = null;
    this.jdCreateApiMessage = null;
    this.jdCreateSuccessMessage = null;
    this.jdCreateInProgress = true;

    const request: CreateJobDescriptionRequest = {
      jd_code: jdCode,
      title,
      required_skills: requiredSkills,
    };

    this.jobDescriptionService
      .createJobDescription(request)
      .pipe(take(1))
      .subscribe((created) => {
        this.jdCreateInProgress = false;

        if (!created) {
          this.jdCreateApiMessage = 'Unable to create JD. Please check JD code uniqueness and try again.';
          return;
        }

        this.loadJobDescriptions(true);
        this.createJdForm.setValue({ jdCode: '', title: '', requiredSkills: '' });
        this.filterForm.controls.jdId.setValue(created.id);
        this.jdCreateSuccessMessage = `JD ${created.jd_code} created successfully.`;
      });
  }

  get summaryItems(): Array<{ label: string; value: string }> {
    const value = this.filterForm.getRawValue();
    const items: Array<{ label: string; value: string }> = [];

    const skills = this.asInputText(value.skills).trim();
    const experienceMin = this.asInputText(value.experienceMin).trim();
    const experienceMax = this.asInputText(value.experienceMax).trim();
    const location = this.asInputText(value.location).trim();
    const preferredLocation = this.asInputText(value.preferredLocation).trim();
    const noticePeriodMax = this.asInputText(value.noticePeriodMax).trim();
    const status = this.asInputText(value.status).trim();
    const degree = this.asInputText(value.degree).trim();
    const certification = this.asInputText(value.certification).trim();
    const resumeUpdatedSince = this.asInputText(value.resumeUpdatedSince).trim();
    const source = this.asInputText(value.source).trim();
    const relevantExperience = this.asInputText(value.relevantExperience).trim();
    const currentCtc = this.asInputText(value.currentCtc).trim();
    const expectedCtc = this.asInputText(value.expectedCtc).trim();
    const previousCompany = this.asInputText(value.previousCompany).trim();
    const employmentStatus = this.asInputText(value.employmentStatus).trim();

    if (value.jdId !== 'any') {
      items.push({ label: 'Job Description', value: this.getJdLabel(value.jdId) });
    }
    if (skills) {
      items.push({ label: 'Skills', value: skills });
    }
    if (experienceMin || experienceMax) {
      items.push({
        label: 'Experience',
        value: `${experienceMin || '0'}-${experienceMax || 'Any'} Years`,
      });
    }
    if (location) {
      items.push({ label: 'Location', value: location });
    }
    if (preferredLocation) {
      items.push({ label: 'Preferred Location', value: preferredLocation });
    }
    if (noticePeriodMax) {
      items.push({ label: 'Notice Period', value: `<= ${noticePeriodMax} Days` });
    }
    if (status && status !== 'any') {
      items.push({ label: 'Status', value: status.replaceAll('_', ' ') });
    }
    if (degree) {
      items.push({ label: 'Degree', value: degree });
    }
    if (certification) {
      items.push({ label: 'Certification', value: certification });
    }
    if (resumeUpdatedSince) {
      items.push({ label: 'Resume Updated', value: `Last ${resumeUpdatedSince} days` });
    }
    if (source) {
      items.push({ label: 'Source', value: source });
    }
    if (relevantExperience) {
      items.push({ label: 'Relevant Experience', value: `${relevantExperience}+ Years` });
    }
    if (currentCtc) {
      items.push({ label: 'Current CTC', value: `>= ${currentCtc}` });
    }
    if (expectedCtc) {
      items.push({ label: 'Expected CTC', value: `>= ${expectedCtc}` });
    }
    if (previousCompany) {
      items.push({ label: 'Previous Company', value: previousCompany });
    }
    if (employmentStatus) {
      items.push({ label: 'Employment Status', value: employmentStatus });
    }

    return items;
  }

  applyFilters(): void {
    const value = this.filterForm.getRawValue();
    const minExperience = this.toOptionalNumber(value.experienceMin);
    const maxExperience = this.toOptionalNumber(value.experienceMax);

    const skills = this.asInputText(value.skills).trim();
    const experienceMin = this.asInputText(value.experienceMin).trim();
    const experienceMax = this.asInputText(value.experienceMax).trim();
    const location = this.asInputText(value.location).trim();
    const preferredLocation = this.asInputText(value.preferredLocation).trim();
    const noticePeriodMax = this.asInputText(value.noticePeriodMax).trim();
    const status = this.asInputText(value.status).trim();
    const degree = this.asInputText(value.degree).trim();
    const certification = this.asInputText(value.certification).trim();
    const resumeUpdatedSince = this.asInputText(value.resumeUpdatedSince).trim();
    const source = this.asInputText(value.source).trim();
    const relevantExperience = this.asInputText(value.relevantExperience).trim();
    const currentCtc = this.asInputText(value.currentCtc).trim();
    const expectedCtc = this.asInputText(value.expectedCtc).trim();
    const previousCompany = this.asInputText(value.previousCompany).trim();
    const employmentStatus = this.asInputText(value.employmentStatus).trim();

    if (minExperience !== undefined && maxExperience !== undefined && minExperience > maxExperience) {
      this.applyValidationMessage = 'Experience minimum must be less than or equal to experience maximum.';
      return;
    }

    this.applyValidationMessage = null;
    const params: Record<string, string> = {};

    if (value.jdId !== 'any') params['jd_id'] = value.jdId;
    if (skills) params['skills'] = skills;
    if (experienceMin) params['experience_min'] = experienceMin;
    if (experienceMax) params['experience_max'] = experienceMax;
    if (location) params['location'] = location;
    if (preferredLocation) params['preferred_location'] = preferredLocation;
    if (noticePeriodMax) params['notice_period_max'] = noticePeriodMax;
    if (status && status !== 'any') params['status'] = status;
    if (degree) params['degree'] = degree;
    if (certification) params['certification'] = certification;
    if (resumeUpdatedSince) params['resume_updated_since'] = resumeUpdatedSince;
    if (source) params['source'] = source;
    if (relevantExperience) params['relevant_experience'] = relevantExperience;
    if (currentCtc) params['current_ctc'] = currentCtc;
    if (expectedCtc) params['expected_ctc'] = expectedCtc;
    if (previousCompany) params['previous_company'] = previousCompany;
    if (employmentStatus) params['employment_status'] = employmentStatus;

    void this.router.navigate(['/candidates'], { queryParams: params });
  }

  clearFilters(): void {
    this.filterForm.patchValue({
      jdId: 'any',
      skills: '',
      experienceMin: '',
      experienceMax: '',
      location: '',
      preferredLocation: '',
      noticePeriodMax: '',
      status: 'any',
      degree: '',
      certification: '',
      resumeUpdatedSince: '',
      source: '',
      relevantExperience: '',
      currentCtc: '',
      expectedCtc: '',
      previousCompany: '',
      employmentStatus: '',
    });
    this.applyValidationMessage = null;
  }

  openSaveModal(): void {
    this.isSaveModalOpen = true;
    this.saveNameControl.setValue('');
    this.saveNameValidationMessage = null;
    this.saveApiMessage = null;
    this.duplicateWarning = null;
  }

  closeSaveModal(): void {
    this.isSaveModalOpen = false;
    this.saveNameValidationMessage = null;
    this.saveApiMessage = null;
    this.duplicateWarning = null;
  }

  confirmSaveFilter(): void {
    const rawName = this.saveNameControl.value.trim();
    if (rawName.length < 3 || rawName.length > 80) {
      this.saveNameValidationMessage = 'Filter name is required and must be 3-80 characters.';
      return;
    }

    this.saveNameValidationMessage = null;
    this.saveApiMessage = null;
    this.duplicateWarning = null;

    const request: SaveFilterRequest = {
      name: rawName,
      jd_id: this.filterForm.controls.jdId.value === 'any' ? null : this.filterForm.controls.jdId.value,
      filter_criteria: this.buildFilterCriteriaPayload(),
    };

    this.savedFilterService
      .createSavedFilter(request)
      .pipe(take(1))
      .subscribe((result) => {
        if (!result) {
          this.saveApiMessage = 'Unable to save filter template. Please try again.';
          return;
        }

        this.duplicateWarning = result.warning;
        this.isSaveModalOpen = false;
      });
  }

  get selectedJdLabel(): string {
    const jdId = this.filterForm.controls.jdId.value;
    if (jdId === 'any') {
      return 'Any / No JD';
    }

    return this.getJdLabel(jdId);
  }

  private buildFilterCriteriaPayload(): Record<string, unknown> {
    const value = this.filterForm.getRawValue();
    const payload: Record<string, unknown> = {};

    const skills = this.asInputText(value.skills).trim();
    const experienceMin = this.asInputText(value.experienceMin).trim();
    const experienceMax = this.asInputText(value.experienceMax).trim();
    const location = this.asInputText(value.location).trim();
    const preferredLocation = this.asInputText(value.preferredLocation).trim();
    const noticePeriodMax = this.asInputText(value.noticePeriodMax).trim();
    const status = this.asInputText(value.status).trim();
    const degree = this.asInputText(value.degree).trim();
    const certification = this.asInputText(value.certification).trim();
    const resumeUpdatedSince = this.asInputText(value.resumeUpdatedSince).trim();
    const source = this.asInputText(value.source).trim();
    const relevantExperience = this.asInputText(value.relevantExperience).trim();
    const currentCtc = this.asInputText(value.currentCtc).trim();
    const expectedCtc = this.asInputText(value.expectedCtc).trim();
    const previousCompany = this.asInputText(value.previousCompany).trim();
    const employmentStatus = this.asInputText(value.employmentStatus).trim();

    if (value.jdId !== 'any') payload['jd_id'] = value.jdId;
    if (skills) payload['skills'] = skills;
    if (experienceMin) payload['experience_min'] = Number(experienceMin);
    if (experienceMax) payload['experience_max'] = Number(experienceMax);
    if (location) payload['location'] = location;
    if (preferredLocation) payload['preferred_location'] = preferredLocation;
    if (noticePeriodMax) payload['notice_period_max'] = Number(noticePeriodMax);
    if (status && status !== 'any') payload['status'] = status;
    if (degree) payload['degree'] = degree;
    if (certification) payload['certification'] = certification;
    if (resumeUpdatedSince) payload['resume_updated_since'] = Number(resumeUpdatedSince);
    if (source) payload['source'] = source;
    if (relevantExperience) payload['relevant_experience'] = Number(relevantExperience);
    if (currentCtc) payload['current_ctc'] = Number(currentCtc);
    if (expectedCtc) payload['expected_ctc'] = Number(expectedCtc);
    if (previousCompany) payload['previous_company'] = previousCompany;
    if (employmentStatus) payload['employment_status'] = employmentStatus;

    return payload;
  }

  private toOptionalNumber(value: unknown): number | undefined {
    const trimmed = this.asInputText(value).trim();
    if (!trimmed) {
      return undefined;
    }

    const parsed = Number(trimmed);
    return Number.isFinite(parsed) ? parsed : undefined;
  }

  private loadJobDescriptions(forceRefresh: boolean = false): void {
    this.jobDescriptionService.listJobDescriptions(forceRefresh).pipe(take(1)).subscribe((items) => {
      this.jobDescriptions = items;
    });
  }

  private asInputText(value: unknown): string {
    if (typeof value === 'string') {
      return value;
    }
    if (typeof value === 'number' && Number.isFinite(value)) {
      return String(value);
    }
    return '';
  }

  private getJdLabel(jdId: string): string {
    const jd = this.jobDescriptions.find((item) => item.id === jdId);
    if (!jd) {
      return 'Selected JD';
    }

    return `${jd.title} (${jd.jd_code})`;
  }

}
