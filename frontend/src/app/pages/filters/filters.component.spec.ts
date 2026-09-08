import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { AuthService } from '../../services/auth.service';
import { JobDescriptionService } from '../../services/job-description.service';
import { SavedFilterService } from '../../services/saved-filter.service';
import { FiltersComponent } from './filters.component';

describe('FiltersComponent', () => {
  let fixture: ComponentFixture<FiltersComponent>;
  let component: FiltersComponent;
  let router: Router;
  let authService: jasmine.SpyObj<AuthService>;
  let jobDescriptionService: jasmine.SpyObj<JobDescriptionService>;
  let savedFilterService: jasmine.SpyObj<SavedFilterService>;

  beforeEach(async () => {
    authService = jasmine.createSpyObj<AuthService>('AuthService', ['logoutFromServer']);
    jobDescriptionService = jasmine.createSpyObj<JobDescriptionService>('JobDescriptionService', [
      'listJobDescriptions',
      'createJobDescription',
    ]);
    savedFilterService = jasmine.createSpyObj<SavedFilterService>('SavedFilterService', ['listSavedFilters', 'createSavedFilter']);
    jobDescriptionService.listJobDescriptions.and.returnValue(
      of([{ id: 'jd-1', jd_code: 'JD-2026-014', title: 'Java Backend Developer' }])
    );
    jobDescriptionService.createJobDescription.and.returnValue(
      of({
        id: 'jd-2',
        jd_code: 'JD-2026-250',
        title: 'Senior Backend Engineer',
        required_skills: ['Python', 'FastAPI', 'SQL'],
        created_at: '2026-08-06T11:00:00Z',
      })
    );
    savedFilterService.listSavedFilters.and.returnValue(of([]));
    savedFilterService.createSavedFilter.and.returnValue(
      of({
        id: 'sf-1',
        recruiter_id: 'r-1',
        name: 'Java Backend Primary',
        jd_id: 'jd-1',
        filter_criteria: { skills: 'Java,Spring Boot' },
        resolved_query_params: { jd_id: 'jd-1', skills: 'Java,Spring Boot' },
        created_at: '2026-08-04T10:00:00Z',
        updated_at: '2026-08-04T10:00:00Z',
        warning: null,
      })
    );

    Object.defineProperty(savedFilterService, 'savedFilters$', {
      get: () => of([]),
    });

    Object.defineProperty(savedFilterService, 'loading$', {
      get: () => of(false),
    });

    await TestBed.configureTestingModule({
      imports: [FiltersComponent, RouterTestingModule],
      providers: [
        { provide: AuthService, useValue: authService },
        { provide: JobDescriptionService, useValue: jobDescriptionService },
        { provide: SavedFilterService, useValue: savedFilterService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(FiltersComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('should update summary values as advanced filter form changes', () => {
    component.filterForm.patchValue({
      certification: 'AWS Certified Developer',
      previousCompany: 'Infosys',
    });

    const summary = component.summaryItems.map((item) => `${item.label}:${item.value}`);
    expect(summary.some((item) => item.includes('Certification:AWS Certified Developer'))).toBeTrue();
    expect(summary.some((item) => item.includes('Previous Company:Infosys'))).toBeTrue();
  });

  it('should create JD from frontend form and refresh dropdown', () => {
    component.createJdForm.setValue({
      jdCode: ' JD-2026-250 ',
      title: ' Senior Backend Engineer ',
      requiredSkills: ' Python, FastAPI, SQL ',
    });

    component.createJobDescription();

    expect(jobDescriptionService.createJobDescription).toHaveBeenCalledWith({
      jd_code: 'JD-2026-250',
      title: 'Senior Backend Engineer',
      required_skills: ['Python', 'FastAPI', 'SQL'],
    });
    expect(jobDescriptionService.listJobDescriptions).toHaveBeenCalledWith(true);
    expect(component.filterForm.controls.jdId.value).toBe('jd-2');
    expect(component.jdCreateSuccessMessage).toContain('JD-2026-250');
  });

  it('should validate JD create form when code or title is missing', () => {
    component.createJdForm.setValue({ jdCode: '', title: 'Backend Engineer', requiredSkills: 'Python' });

    component.createJobDescription();

    expect(jobDescriptionService.createJobDescription).not.toHaveBeenCalled();
    expect(component.jdCreateValidationMessage).toContain('required');
  });

  it('should navigate to candidates with full criteria query params on apply', async () => {
    const navigateSpy = spyOn(router, 'navigate').and.resolveTo(true);

    component.filterForm.patchValue({
      jdId: 'jd-1',
      skills: 'Java, Spring Boot',
      experienceMin: '4',
      experienceMax: '8',
      location: 'Bengaluru',
      preferredLocation: 'Hyderabad',
      degree: 'Bachelor',
      certification: 'AWS',
      resumeUpdatedSince: '30',
      source: 'referral',
      relevantExperience: '5',
      currentCtc: '10',
      expectedCtc: '14',
      previousCompany: 'Infosys',
      employmentStatus: 'employed',
      status: 'open_to_opportunities',
    });

    component.applyFilters();

    expect(navigateSpy).toHaveBeenCalledWith(['/candidates'], {
      queryParams: jasmine.objectContaining({
        jd_id: 'jd-1',
        skills: 'Java, Spring Boot',
        experience_min: '4',
        experience_max: '8',
        location: 'Bengaluru',
        preferred_location: 'Hyderabad',
        degree: 'Bachelor',
        certification: 'AWS',
        resume_updated_since: '30',
        source: 'referral',
        relevant_experience: '5',
        current_ctc: '10',
        expected_ctc: '14',
        previous_company: 'Infosys',
        employment_status: 'employed',
        status: 'open_to_opportunities',
      }),
    });
  });

  it('should not include status when status is Any', () => {
    const navigateSpy = spyOn(router, 'navigate').and.resolveTo(true);

    component.filterForm.patchValue({
      status: 'any',
      location: 'Bengaluru',
    });

    component.applyFilters();

    const [, options] = navigateSpy.calls.mostRecent().args;
    const queryParams = ((options as { queryParams?: Record<string, string> } | undefined)?.queryParams) ?? {};
    expect(queryParams['status']).toBeUndefined();
    expect(queryParams['location']).toBe('Bengaluru');
  });

  it('should block apply when experience min is greater than max', () => {
    const navigateSpy = spyOn(router, 'navigate').and.resolveTo(true);

    component.filterForm.patchValue({
      experienceMin: '8',
      experienceMax: '3',
    });

    component.applyFilters();

    expect(navigateSpy).not.toHaveBeenCalled();
    expect(component.applyValidationMessage).toContain('Experience minimum must be less than or equal to experience maximum');
  });

  it('should prevent save when template name is blank', () => {
    component.openSaveModal();
    component.saveNameControl.setValue('  ');

    component.confirmSaveFilter();

    expect(savedFilterService.createSavedFilter).not.toHaveBeenCalled();
    expect(component.saveNameValidationMessage).toContain('required');
  });

  it('should submit save request with jd and filter criteria', () => {
    component.filterForm.patchValue({
      jdId: 'jd-1',
      skills: 'Java, Spring Boot',
      location: 'Bengaluru',
    });

    component.openSaveModal();
    component.saveNameControl.setValue('Java Backend Primary');
    component.confirmSaveFilter();

    expect(savedFilterService.createSavedFilter).toHaveBeenCalledWith(
      jasmine.objectContaining({
        name: 'Java Backend Primary',
        jd_id: 'jd-1',
        filter_criteria: jasmine.objectContaining({
          jd_id: 'jd-1',
          skills: 'Java, Spring Boot',
          location: 'Bengaluru',
        }),
      })
    );
  });

});
