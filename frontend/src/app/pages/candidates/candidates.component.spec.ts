import { of } from 'rxjs';

import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { CandidateService } from '../../services/candidate.service';
import { IntegrationService } from '../../services/integration.service';
import { JobDescriptionService } from '../../services/job-description.service';
import { AuthService } from '../../services/auth.service';
import { SavedFilterService } from '../../services/saved-filter.service';
import { ShortlistService } from '../../services/shortlist.service';
import { CandidatesComponent } from './candidates.component';

describe('CandidatesComponent', () => {
  let fixture: ComponentFixture<CandidatesComponent>;
  let component: CandidatesComponent;
  let candidateService: jasmine.SpyObj<CandidateService>;
  let integrationService: jasmine.SpyObj<IntegrationService>;
  let jobDescriptionService: jasmine.SpyObj<JobDescriptionService>;
  let authService: jasmine.SpyObj<AuthService>;
  let savedFilterService: jasmine.SpyObj<SavedFilterService>;
  let shortlistService: jasmine.SpyObj<ShortlistService>;

  const responseForPage = (page: number) => ({
    items: [
      {
        id: `11111111-1111-1111-1111-11111111111${page}`,
        zoho_candidate_id: `z-${page}`,
        full_name: page === 1 ? 'Arjun Kumar' : 'Priya Sharma',
        skills: ['Java', 'Spring Boot'],
        total_experience_years: 6,
        current_location: 'Bengaluru',
        current_company: 'TechNova Solutions',
        notice_period_days: 30,
        status: 'active',
        match_percentage: 92,
        updated_at: '2026-07-28T10:30:00Z',
      },
    ],
    page,
    page_size: 10,
    total_items: 2,
    total_pages: 2,
    q: null,
    sort_by: 'full_name',
    sort_order: 'asc' as const,
  });

  beforeEach(async () => {
    candidateService = jasmine.createSpyObj<CandidateService>('CandidateService', ['loadCandidates']);
    integrationService = jasmine.createSpyObj<IntegrationService>('IntegrationService', ['pollZohoStatus']);
    jobDescriptionService = jasmine.createSpyObj<JobDescriptionService>('JobDescriptionService', ['listJobDescriptions']);
    authService = jasmine.createSpyObj<AuthService>('AuthService', ['logoutFromServer']);
    savedFilterService = jasmine.createSpyObj<SavedFilterService>('SavedFilterService', ['listSavedFilters']);
    shortlistService = jasmine.createSpyObj<ShortlistService>('ShortlistService', ['createShortlist']);

    Object.defineProperty(candidateService, 'loading$', {
      get: () => of(false),
    });
    Object.defineProperty(candidateService, 'error$', {
      get: () => of(null),
    });
    Object.defineProperty(savedFilterService, 'savedFilters$', {
      get: () => of([]),
    });

    candidateService.loadCandidates.and.callFake((query) => {
      return of(responseForPage(query.page));
    });

    integrationService.pollZohoStatus.and.returnValue(
      of({
        integration: 'Zoho Recruit',
        connection_state: 'connected',
        status: 'healthy',
        access_level: 'read_only',
        sync_type: 'manual',
        last_successful_sync_at: '2026-07-28T10:30:00Z',
        last_checked_at: new Date().toISOString(),
      })
    );

    jobDescriptionService.listJobDescriptions.and.returnValue(
      of([
        { id: 'jd-1', jd_code: 'JD-2026-014', title: 'Java Backend Developer' },
        { id: 'jd-2', jd_code: 'JD-2026-101', title: 'Python API Developer' },
      ])
    );
    savedFilterService.listSavedFilters.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [CandidatesComponent, RouterTestingModule],
      providers: [
        { provide: CandidateService, useValue: candidateService },
        { provide: IntegrationService, useValue: integrationService },
        { provide: JobDescriptionService, useValue: jobDescriptionService },
        { provide: AuthService, useValue: authService },
        { provide: SavedFilterService, useValue: savedFilterService },
        { provide: ShortlistService, useValue: shortlistService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CandidatesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should debounce search input before reloading candidates', fakeAsync(() => {
    expect(candidateService.loadCandidates).toHaveBeenCalledWith(
      jasmine.objectContaining({ page: 1, pageSize: 10 })
    );

    candidateService.loadCandidates.calls.reset();
    component.searchControl.setValue('  python  ');
    tick(299);
    expect(candidateService.loadCandidates).not.toHaveBeenCalled();

    tick(1);
    expect(candidateService.loadCandidates).toHaveBeenCalledWith(
      jasmine.objectContaining({ q: 'python', page: 1, pageSize: 10 })
    );
  }));

  it('should submit search immediately and navigate pages', () => {
    candidateService.loadCandidates.calls.reset();
    component.searchControl.setValue('TechNova', { emitEvent: false });
    component.onSearchSubmit();

    expect(candidateService.loadCandidates).toHaveBeenCalledWith(
      jasmine.objectContaining({ q: 'TechNova', page: 1, pageSize: 10 })
    );

    candidateService.loadCandidates.calls.reset();
    component.onPageChange(2);

    expect(candidateService.loadCandidates).toHaveBeenCalledWith(
      jasmine.objectContaining({ page: 2, pageSize: 10 })
    );
  });

  it('should toggle filter panel visibility', () => {
    expect(component.isFilterPanelOpen).toBeFalse();

    component.toggleFilters();
    expect(component.isFilterPanelOpen).toBeTrue();

    component.toggleFilters();
    expect(component.isFilterPanelOpen).toBeFalse();
  });

  it('should show a three-page window around the active page', () => {
    component.totalPages = 8;
    component.page = 4;

    expect(component.paginationPages).toEqual([3, 4, 5]);
  });

  it('should apply a saved filter through its existing resolved query parameters', () => {
    const router = TestBed.inject(Router);
    const navigate = spyOn(router, 'navigate').and.resolveTo(true);
    const template = {
      id: 'filter-1',
      recruiter_id: 'recruiter-1',
      name: 'Full stack Dotnet developer',
      jd_id: null,
      filter_criteria: { skills: 'angular, .net, sql server' },
      resolved_query_params: { skills: 'angular, .net, sql server', experience_min: '5' },
      created_at: '2026-08-17T12:11:15Z',
      updated_at: '2026-08-17T12:11:15Z',
      warning: null,
    };

    component.isFilterPanelOpen = true;
    component.savedFiltersOpen = true;
    component.applySavedFilter(template);

    expect(navigate).toHaveBeenCalledWith(['/candidates'], { queryParams: template.resolved_query_params });
    expect(component.savedFiltersOpen).toBeFalse();
    expect(component.isFilterPanelOpen).toBeFalse();
  });

  it('should call API with filter params when apply filters is clicked', () => {
    candidateService.loadCandidates.calls.reset();
    component.basicFilterForm.setValue({
      jdId: 'jd-1',
      skills: 'Java, Spring Boot',
      experienceMin: '4',
      experienceMax: '8',
      location: 'Bengaluru',
      preferredLocation: 'Hyderabad',
      noticePeriodMax: '30',
      status: 'active',
    });

    component.isFilterPanelOpen = true;
    component.applyFilters();

    expect(candidateService.loadCandidates).toHaveBeenCalledWith(
      jasmine.objectContaining({
        page: 1,
        jdId: 'jd-1',
        skills: ['Java', 'Spring Boot'],
        experienceMin: 4,
        experienceMax: 8,
        location: 'Bengaluru',
        preferredLocation: 'Hyderabad',
        noticePeriodMax: 30,
        status: 'active',
      })
    );
    expect(component.activeFilterChips.length).toBeGreaterThan(0);
    expect(component.isFilterPanelOpen).toBeFalse();
  });

  it('should cancel active filters and remove their query parameters', () => {
    const router = TestBed.inject(Router);
    const navigate = spyOn(router, 'navigate').and.resolveTo(true);
    component.searchTerm = 'python';
    component.basicFilterForm.controls.skills.setValue('Python');
    component.activeFilterChips = ['Skills: Python'];

    component.cancelActiveFilters();

    expect(component.activeFilterChips).toEqual([]);
    expect(component.basicFilterForm.controls.skills.value).toBe('');
    expect(navigate).toHaveBeenCalledWith(['/candidates'], { queryParams: { q: 'python' } });
  });

  it('should prevent apply when min experience exceeds max experience', () => {
    candidateService.loadCandidates.calls.reset();
    component.basicFilterForm.setValue({
      jdId: 'any',
      skills: '',
      experienceMin: '10',
      experienceMax: '4',
      location: '',
      preferredLocation: '',
      noticePeriodMax: '',
      status: 'any',
    });

    component.applyFilters();

    expect(candidateService.loadCandidates).not.toHaveBeenCalled();
    expect(component.filterValidationMessage).toContain('Experience minimum must be less than or equal to experience maximum');
  });
});
