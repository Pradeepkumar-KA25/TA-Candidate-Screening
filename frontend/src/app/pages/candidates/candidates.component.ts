import { CommonModule } from '@angular/common';
import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { debounceTime, distinctUntilChanged } from 'rxjs';
import { firstValueFrom } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { CandidateListItem, CandidateListQuery, CandidateListResponse } from '../../models/candidate.models';
import { JobDescriptionListItem } from '../../models/job-description.models';
import { ZohoIntegrationStatus } from '../../models/integration.models';
import { SavedFilterItem } from '../../models/saved-filter.models';
import { AuthService } from '../../services/auth.service';
import { CandidateService } from '../../services/candidate.service';
import { IntegrationService } from '../../services/integration.service';
import { JobDescriptionService } from '../../services/job-description.service';
import { SavedFilterService } from '../../services/saved-filter.service';
import { ShortlistService } from '../../services/shortlist.service';
import { sanitizeCandidateName, sanitizeDisplayText, summarizeSkills } from '../../utils/display-format';

@Component({
  selector: 'app-candidates',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './candidates.component.html',
  styleUrl: './candidates.component.css',
})
export class CandidatesComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  readonly searchControl = new FormControl<string>('', { nonNullable: true });
  readonly basicFilterForm = new FormGroup({
    jdId: new FormControl<string>('any', { nonNullable: true }),
    skills: new FormControl<string>('', { nonNullable: true }),
    experienceMin: new FormControl<string>('', { nonNullable: true }),
    experienceMax: new FormControl<string>('', { nonNullable: true }),
    location: new FormControl<string>('', { nonNullable: true }),
    preferredLocation: new FormControl<string>('', { nonNullable: true }),
    noticePeriodMax: new FormControl<string>('', { nonNullable: true }),
    status: new FormControl<string>('any', { nonNullable: true }),
  });

  candidates: CandidateListItem[] = [];
  zohoStatus: ZohoIntegrationStatus | null = null;
  loading = false;
  errorMessage: string | null = null;
  searchTerm = '';
  page = 1;
  pageSize = 10;
  totalItems = 0;
  totalPages = 0;
  sortBy = '';
  sortOrder: 'asc' | 'desc' | '' = '';
  isFilterPanelOpen = false;
  filterValidationMessage: string | null = null;
  activeFilterChips: string[] = [];
  jobDescriptions: JobDescriptionListItem[] = [];
  savedTemplates: SavedFilterItem[] = [];
  savedFiltersOpen = false;
  selectedCandidateIds: Set<string> = new Set();
  selectedShortlistJdId: string | null = null;
  movingToShortlist = false;
  deletingCandidates = false;
  selectingAllCandidates = false;
  showDeleteConfirmModal = false;
  deleteConfirmCount = 0;
  private advancedCriteria: {
    degree?: string;
    certification?: string;
    resumeUpdatedSince?: number;
    source?: string;
    relevantExperience?: number;
    currentCtc?: number;
    expectedCtc?: number;
    previousCompany?: string;
    employmentStatus?: string;
  } = {};

  constructor(
    private readonly authService: AuthService,
    private readonly candidateService: CandidateService,
    private readonly integrationService: IntegrationService,
    private readonly jobDescriptionService: JobDescriptionService,
    private readonly savedFilterService: SavedFilterService,
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

    this.candidateService.loading$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((loading) => {
      this.loading = loading;
    });

    this.candidateService.error$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((message) => {
      this.errorMessage = message;
    });

    this.searchControl.valueChanges
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe((value) => {
        this.applySearch(value, true);
      });
  }

  ngOnInit(): void {
    this.savedFilterService.savedFilters$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((items) => {
        this.savedTemplates = items;
      });
    this.savedFilterService.listSavedFilters().pipe(takeUntilDestroyed(this.destroyRef)).subscribe();

    this.jobDescriptionService
      .listJobDescriptions()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((items) => {
        this.jobDescriptions = items;
        if (!this.selectedShortlistJdId && items.length > 0) {
          this.selectedShortlistJdId = items[0].id;
        }
      });

    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const q = params.get('q')?.trim() ?? '';
      this.searchTerm = q;
      this.searchControl.setValue(q, { emitEvent: false });

      const jdId = params.get('jd_id') ?? 'any';
      const skills = params.get('skills') ?? '';
      const experienceMin = params.get('experience_min') ?? '';
      const experienceMax = params.get('experience_max') ?? '';
      const location = params.get('location') ?? '';
      const preferredLocation = params.get('preferred_location') ?? '';
      const noticePeriodMax = params.get('notice_period_max') ?? '';
      const status = params.get('status') ?? 'any';

      this.basicFilterForm.patchValue(
        {
          jdId,
          skills,
          experienceMin,
          experienceMax,
          location,
          preferredLocation,
          noticePeriodMax,
          status,
        },
        { emitEvent: false }
      );

      this.advancedCriteria = {
        degree: params.get('degree')?.trim() || undefined,
        certification: params.get('certification')?.trim() || undefined,
        resumeUpdatedSince: this.toOptionalNumber(params.get('resume_updated_since')),
        source: params.get('source')?.trim() || undefined,
        relevantExperience: this.toOptionalNumber(params.get('relevant_experience')),
        currentCtc: this.toOptionalNumber(params.get('current_ctc')),
        expectedCtc: this.toOptionalNumber(params.get('expected_ctc')),
        previousCompany: params.get('previous_company')?.trim() || undefined,
        employmentStatus: params.get('employment_status')?.trim() || undefined,
      };

      this.isFilterPanelOpen = false;

      const basicCriteria = this.getNormalizedFilterCriteria();
      this.activeFilterChips = this.buildFilterChips({ ...basicCriteria, ...this.advancedCriteria });
      this.loadCandidates(1, this.searchTerm, basicCriteria);
    });
  }

  get isConnected(): boolean {
    return this.zohoStatus?.connection_state === 'connected';
  }

  get formattedSyncTime(): string {
    if (!this.zohoStatus?.last_successful_sync_at) {
      return 'Not synced yet';
    }

    return new Date(this.zohoStatus.last_successful_sync_at).toLocaleString();
  }

  get startItem(): number {
    if (!this.totalItems) {
      return 0;
    }

    return (this.page - 1) * this.pageSize + 1;
  }

  get endItem(): number {
    return Math.min(this.page * this.pageSize, this.totalItems);
  }

  get paginationPages(): number[] {
    const totalPages = this.totalPages || 1;
    const visibleWindow = 3;
    if (totalPages <= visibleWindow) {
      return Array.from({ length: totalPages }, (_, index) => index + 1);
    }

    const currentIndex = this.page - 1;
    const halfWindow = Math.floor(visibleWindow / 2);
    let start = Math.max(0, currentIndex - halfWindow);
    let end = Math.min(totalPages, start + visibleWindow);

    start = Math.max(0, end - visibleWindow);

    return Array.from({ length: end - start }, (_, index) => start + index + 1);
  }

  onSearchSubmit(): void {
    this.applySearch(this.searchControl.value, false);
  }

  onLogout(): void {
    this.authService.logoutFromServer().pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.router.navigate(['/login']);
    });
  }

  goBack(): void {
    window.history.back();
  }

  onPageChange(nextPage: number): void {
    if (nextPage < 1 || nextPage > this.totalPages) {
      return;
    }

    this.loadCandidates(nextPage);
  }

  onPageSizeChange(value: string): void {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed < 1) {
      return;
    }

    this.pageSize = parsed;
    this.loadCandidates(1);
  }

  onSortChange(value: string): void {
    if (!value) {
      this.sortBy = '';
      this.sortOrder = '';
      this.loadCandidates(1);
      return;
    }

    const [sortBy, sortOrder] = value.split(':');
    this.sortBy = sortBy || '';
    this.sortOrder = sortOrder === 'desc' ? 'desc' : 'asc';
    this.loadCandidates(1);
  }

  toggleFilters(): void {
    this.isFilterPanelOpen = !this.isFilterPanelOpen;
  }

  toggleSavedFilters(): void {
    this.savedFiltersOpen = !this.savedFiltersOpen;
  }

  applySavedFilter(template: SavedFilterItem): void {
    this.savedFiltersOpen = false;
    this.isFilterPanelOpen = false;
    void this.router.navigate(['/candidates'], {
      queryParams: template.resolved_query_params,
    });
  }

  cancelActiveFilters(): void {
    const searchTerm = this.searchTerm;
    this.clearBasicFilters(false);
    this.isFilterPanelOpen = false;
    this.savedFiltersOpen = false;
    void this.router.navigate(['/candidates'], {
      queryParams: searchTerm ? { q: searchTerm } : {},
    });
  }

  clearBasicFilters(reloadCandidates: boolean = true): void {
    this.basicFilterForm.setValue({
      jdId: 'any',
      skills: '',
      experienceMin: '',
      experienceMax: '',
      location: '',
      preferredLocation: '',
      noticePeriodMax: '',
      status: 'any',
    });
    this.filterValidationMessage = null;
    this.advancedCriteria = {};
    this.activeFilterChips = [];
    this.selectedCandidateIds.clear();
    if (reloadCandidates) {
      this.loadCandidates(1);
    }
  }

  toggleCandidateSelection(candidateId: string): void {
    if (this.selectedCandidateIds.has(candidateId)) {
      this.selectedCandidateIds.delete(candidateId);
    } else {
      this.selectedCandidateIds.add(candidateId);
    }
  }

  toggleSelectAll(): void {
    if (this.isAllSelected()) {
      this.selectedCandidateIds.clear();
      return;
    }

    // If not all selected, load all candidates and select them
    if (this.selectedCandidateIds.size === 0) {
      this.selectingAllCandidates = true;

      // Parse skills from comma-separated string to array
      const skillsText = this.basicFilterForm.get('skills')?.value || '';
      const skillsArray = skillsText
        .split(',')
        .map((item) => item.trim())
        .filter((item) => item.length > 0);
      
      // Build current query to maintain filters
      const query: CandidateListQuery = {
        page: 1,
        pageSize: this.totalItems > 0 ? Math.min(this.totalItems, 10000) : 10000, // Load all candidates
        q: this.searchTerm || undefined,
        sortBy: this.sortBy || undefined,
        sortOrder: this.sortOrder || undefined,
        jdId: this.basicFilterForm.get('jdId')?.value === 'any' ? undefined : this.basicFilterForm.get('jdId')?.value,
        skills: skillsArray.length > 0 ? skillsArray : undefined,
        experienceMin: this.basicFilterForm.get('experienceMin')?.value ? Number(this.basicFilterForm.get('experienceMin')?.value) : undefined,
        experienceMax: this.basicFilterForm.get('experienceMax')?.value ? Number(this.basicFilterForm.get('experienceMax')?.value) : undefined,
        location: this.basicFilterForm.get('location')?.value || undefined,
        preferredLocation: this.basicFilterForm.get('preferredLocation')?.value || undefined,
        noticePeriodMax: this.basicFilterForm.get('noticePeriodMax')?.value ? Number(this.basicFilterForm.get('noticePeriodMax')?.value) : undefined,
        status: this.basicFilterForm.get('status')?.value === 'any' ? undefined : this.basicFilterForm.get('status')?.value,
        degree: this.advancedCriteria.degree,
        certification: this.advancedCriteria.certification,
        resumeUpdatedSince: this.advancedCriteria.resumeUpdatedSince,
        source: this.advancedCriteria.source,
        relevantExperience: this.advancedCriteria.relevantExperience,
        currentCtc: this.advancedCriteria.currentCtc,
        expectedCtc: this.advancedCriteria.expectedCtc,
        previousCompany: this.advancedCriteria.previousCompany,
        employmentStatus: this.advancedCriteria.employmentStatus,
      };

      this.candidateService
        .loadCandidates(query)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (response) => {
            this.selectedCandidateIds.clear();
            response.items.forEach((candidate) => this.selectedCandidateIds.add(candidate.id));
            this.selectingAllCandidates = false;
          },
          error: () => {
            this.selectingAllCandidates = false;
            this.errorMessage = 'Failed to select all candidates';
          },
        });
    }
  }

  isCandidateSelected(candidateId: string): boolean {
    return this.selectedCandidateIds.has(candidateId);
  }

  getSelectionCount(): number {
    return this.selectedCandidateIds.size;
  }

  isAllSelected(): boolean {
    return this.totalItems > 0 && this.selectedCandidateIds.size === this.totalItems;
  }

  isIndeterminate(): boolean {
    return this.selectedCandidateIds.size > 0 && this.selectedCandidateIds.size < this.totalItems;
  }

  async moveSelectedToShortlist(): Promise<void> {
    if (!this.selectedShortlistJdId || this.selectedCandidateIds.size === 0 || this.movingToShortlist) {
      return;
    }

    this.movingToShortlist = true;
    this.errorMessage = null;

    try {
      await firstValueFrom(
        this.shortlistService.createShortlist(this.selectedShortlistJdId, Array.from(this.selectedCandidateIds))
      );
      const jdId = this.selectedShortlistJdId;
      this.selectedCandidateIds.clear();
      this.router.navigate(['/shortlists'], { queryParams: { jd_id: jdId } });
    } catch {
      this.errorMessage = 'Unable to move selected candidates to shortlist. Please try again.';
    } finally {
      this.movingToShortlist = false;
    }
  }

  async deleteSelectedCandidates(): Promise<void> {
    if (this.selectedCandidateIds.size === 0 || this.deletingCandidates) {
      return;
    }

    // Show confirmation modal instead of browser alert
    this.deleteConfirmCount = this.selectedCandidateIds.size;
    this.showDeleteConfirmModal = true;
  }

  async confirmDelete(): Promise<void> {
    if (this.selectedCandidateIds.size === 0 || this.deletingCandidates) {
      return;
    }

    this.showDeleteConfirmModal = false;
    this.deletingCandidates = true;
    this.errorMessage = null;

    try {
      // Use batch delete endpoint which handles unlimited candidates
      const deleteResponse = await firstValueFrom(
        this.candidateService.deleteCandidatesBatch(Array.from(this.selectedCandidateIds))
      );

      this.selectedCandidateIds.clear();
      this.loadCandidates(this.page, this.searchTerm);
    } catch {
      this.errorMessage = 'Unable to delete selected candidates. Please try again.';
    } finally {
      this.deletingCandidates = false;
    }
  }

  cancelDelete(): void {
    this.showDeleteConfirmModal = false;
    this.deleteConfirmCount = 0;
  }

  applyFilters(): void {
    const criteria = this.getNormalizedFilterCriteria();
    const hasInvalidRange =
      criteria.experienceMin !== undefined &&
      criteria.experienceMax !== undefined &&
      criteria.experienceMin > criteria.experienceMax;

    if (hasInvalidRange) {
      this.filterValidationMessage = 'Experience minimum must be less than or equal to experience maximum.';
      return;
    }

    this.filterValidationMessage = null;
    this.activeFilterChips = this.buildFilterChips({ ...criteria, ...this.advancedCriteria });
    this.isFilterPanelOpen = false;
    this.loadCandidates(1, this.searchTerm, criteria);
  }

  toggleSortOrder(): void {
    this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
    this.loadCandidates(1);
  }

  statusLabel(status: string): string {
    return status.replaceAll('_', ' ');
  }

  statusClass(status: string): string {
    if (status === 'open_to_opportunities') {
      return 'badge-info';
    }

    return 'badge-success';
  }

  experienceLabel(candidate: CandidateListItem): string {
    return candidate.total_experience_years === null ? '—' : `${candidate.total_experience_years} Years`;
  }

  noticePeriodLabel(candidate: CandidateListItem): string {
    return candidate.notice_period_days === null ? '—' : `${candidate.notice_period_days} Days`;
  }

  matchLabel(candidate: CandidateListItem): string {
    return candidate.match_percentage === null ? '—' : `${Math.round(candidate.match_percentage)}%`;
  }

  safeCandidateName(value: string | null | undefined): string {
    return sanitizeCandidateName(value);
  }

  safeText(value: string | null | undefined): string {
    return sanitizeDisplayText(value);
  }

  skillSummary(candidate: CandidateListItem): string {
    return summarizeSkills(candidate.skills);
  }

  private applySearch(value: string, fromTyping: boolean): void {
    const trimmed = value.trim();
    if (fromTyping || trimmed !== this.searchTerm) {
      this.searchTerm = trimmed;
      this.loadCandidates(1, trimmed);
    }
  }

  private getNormalizedFilterCriteria(): {
    jdId?: string;
    skills?: string[];
    experienceMin?: number;
    experienceMax?: number;
    location?: string;
    preferredLocation?: string;
    noticePeriodMax?: number;
    status?: string;
  } {
    const formValue = this.basicFilterForm.getRawValue();
    const normalizedSkills = this.asText(formValue.skills)
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item.length > 0);

    const experienceMin = this.toOptionalNumberFromUnknown(formValue.experienceMin);
    const experienceMax = this.toOptionalNumberFromUnknown(formValue.experienceMax);
    const noticePeriodMax = this.toOptionalNumberFromUnknown(formValue.noticePeriodMax);
    const status = this.asText(formValue.status).trim();

    return {
      jdId: formValue.jdId !== 'any' ? formValue.jdId : undefined,
      skills: normalizedSkills.length > 0 ? normalizedSkills : undefined,
      experienceMin,
      experienceMax,
      location: this.asOptionalText(formValue.location),
      preferredLocation: this.asOptionalText(formValue.preferredLocation),
      noticePeriodMax,
      status: status && status !== 'any' ? status : undefined,
    };
  }

  private asText(value: unknown): string {
    if (typeof value === 'string') {
      return value;
    }
    if (typeof value === 'number' && Number.isFinite(value)) {
      return String(value);
    }
    return '';
  }

  private asOptionalText(value: unknown): string | undefined {
    const text = this.asText(value).trim();
    return text || undefined;
  }

  private toOptionalNumberFromUnknown(value: unknown): number | undefined {
    const text = this.asText(value).trim();
    if (!text) {
      return undefined;
    }

    const parsed = Number(text);
    return Number.isFinite(parsed) ? parsed : undefined;
  }

  private buildFilterChips(criteria: {
    jdId?: string;
    skills?: string[];
    experienceMin?: number;
    experienceMax?: number;
    location?: string;
    preferredLocation?: string;
    noticePeriodMax?: number;
    status?: string;
    degree?: string;
    certification?: string;
    resumeUpdatedSince?: number;
    source?: string;
    relevantExperience?: number;
    currentCtc?: number;
    expectedCtc?: number;
    previousCompany?: string;
    employmentStatus?: string;
  }): string[] {
    const chips: string[] = [];
    if (criteria.jdId) {
      chips.push(`Job Description: ${this.getJdLabel(criteria.jdId)}`);
    }
    if (criteria.skills && criteria.skills.length > 0) {
      chips.push(`Skills: ${criteria.skills.join(', ')}`);
    }
    if (criteria.experienceMin !== undefined || criteria.experienceMax !== undefined) {
      chips.push(`Experience: ${criteria.experienceMin ?? 0}-${criteria.experienceMax ?? 'Any'} Years`);
    }
    if (criteria.location) {
      chips.push(`Current Location: ${criteria.location}`);
    }
    if (criteria.preferredLocation) {
      chips.push(`Preferred Location: ${criteria.preferredLocation}`);
    }
    if (criteria.noticePeriodMax !== undefined) {
      chips.push(`Notice: <= ${criteria.noticePeriodMax} Days`);
    }
    if (criteria.status) {
      chips.push(`Status: ${criteria.status.replaceAll('_', ' ')}`);
    }
    if (criteria.degree) {
      chips.push(`Degree: ${criteria.degree}`);
    }
    if (criteria.certification) {
      chips.push(`Certification: ${criteria.certification}`);
    }
    if (criteria.resumeUpdatedSince !== undefined) {
      chips.push(`Resume Updated: Last ${criteria.resumeUpdatedSince} Days`);
    }
    if (criteria.source) {
      chips.push(`Source: ${criteria.source}`);
    }
    if (criteria.relevantExperience !== undefined) {
      chips.push(`Relevant Experience: ${criteria.relevantExperience}+ Years`);
    }
    if (criteria.currentCtc !== undefined) {
      chips.push(`Current CTC: >= ${criteria.currentCtc}`);
    }
    if (criteria.expectedCtc !== undefined) {
      chips.push(`Expected CTC: >= ${criteria.expectedCtc}`);
    }
    if (criteria.previousCompany) {
      chips.push(`Previous Company: ${criteria.previousCompany}`);
    }
    if (criteria.employmentStatus) {
      chips.push(`Employment Status: ${criteria.employmentStatus}`);
    }
    return chips;
  }

  private loadCandidates(
    page: number,
    query: string = this.searchTerm,
    criteria: {
      jdId?: string;
      skills?: string[];
      experienceMin?: number;
      experienceMax?: number;
      location?: string;
      preferredLocation?: string;
      noticePeriodMax?: number;
      status?: string;
    } = this.getNormalizedFilterCriteria()
  ): void {
    const request: CandidateListQuery = {
      q: query || undefined,
      page,
      pageSize: this.pageSize,
      sortBy: this.sortBy || undefined,
      sortOrder: this.sortOrder || undefined,
      ...criteria,
      ...this.advancedCriteria,
    };

    this.candidateService
      .loadCandidates(request)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((response: CandidateListResponse) => {
        this.page = response.page;
        this.pageSize = response.page_size;
        this.totalItems = response.total_items;
        this.totalPages = response.total_pages;
        this.searchTerm = response.q ?? '';
        this.candidates = response.items;

        const visibleCandidateIds = new Set(response.items.map((item) => item.id));
        Array.from(this.selectedCandidateIds).forEach((id) => {
          if (!visibleCandidateIds.has(id)) {
            this.selectedCandidateIds.delete(id);
          }
        });
      });
  }

  private toOptionalNumber(value: string | null): number | undefined {
    if (!value || value.trim() === '') {
      return undefined;
    }

    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  }

  private getJdLabel(jdId: string): string {
    const jd = this.jobDescriptions.find((item) => item.id === jdId);
    if (!jd) {
      return 'Selected JD';
    }

    return `${jd.title} (${jd.jd_code})`;
  }
}
