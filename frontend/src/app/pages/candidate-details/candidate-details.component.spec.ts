import { of } from 'rxjs';

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';

import { CandidateService } from '../../services/candidate.service';
import { IntegrationService } from '../../services/integration.service';
import { CandidateDetailsComponent } from './candidate-details.component';

describe('CandidateDetailsComponent', () => {
  let fixture: ComponentFixture<CandidateDetailsComponent>;
  let candidateService: jasmine.SpyObj<CandidateService>;
  let integrationService: jasmine.SpyObj<IntegrationService>;

  beforeEach(async () => {
    candidateService = jasmine.createSpyObj<CandidateService>('CandidateService', ['loadCandidateDetails']);
    integrationService = jasmine.createSpyObj<IntegrationService>('IntegrationService', ['pollZohoStatus']);

    Object.defineProperty(candidateService, 'error$', {
      get: () => of(null),
    });

    candidateService.loadCandidateDetails.and.returnValue(
      of({
        id: '11111111-1111-1111-1111-111111111111',
        zoho_candidate_id: 'z-1',
        full_name: 'Arjun Kumar',
        email: 'arjun@example.com',
        phone: '+91 98XXXXXX10',
        total_experience_years: 6,
        relevant_experience_years: 5,
        current_company: 'TechNova Solutions',
        current_location: 'Bengaluru',
        preferred_location: 'Bengaluru',
        notice_period_days: 30,
        skills: ['Java', 'Spring Boot'],
        degree: 'B.E. CSE',
        normalized_degree: 'Bachelor Degree - Computer Science',
        current_ctc: 10,
        expected_ctc: 14,
        status: 'active',
        source: 'zoho_recruit',
        created_at: '2026-07-28T10:30:00Z',
        updated_at: '2026-07-29T10:30:00Z',
        normalized_data: [
          { field: 'current_location', raw_value: 'Bangalore', normalized_value: 'Bengaluru' },
        ],
        match_context: {
          jd_id: 'JD-2026-014',
          jd_title: 'Java Backend Developer',
          match_percentage: 92,
          match_score: 92,
          matched_criteria: ['Java'],
          metadata: {},
        },
      })
    );

    integrationService.pollZohoStatus.and.returnValue(
      of({
        integration: 'Zoho Recruit',
        connection_state: 'connected',
        status: 'healthy',
        access_level: 'read_only',
        sync_type: 'manual',
        last_successful_sync_at: '2026-07-29T10:30:00Z',
        last_checked_at: '2026-07-29T10:30:00Z',
      })
    );

    await TestBed.configureTestingModule({
      imports: [CandidateDetailsComponent],
      providers: [
        { provide: CandidateService, useValue: candidateService },
        { provide: IntegrationService, useValue: integrationService },
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of(convertToParamMap({ id: '11111111-1111-1111-1111-111111111111' })),
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CandidateDetailsComponent);
    fixture.detectChanges();
  });

  it('should load candidate profile from route id and render normalized data', () => {
    expect(candidateService.loadCandidateDetails).toHaveBeenCalledWith('11111111-1111-1111-1111-111111111111');
    expect(fixture.nativeElement.textContent).toContain('Arjun Kumar');
    expect(fixture.nativeElement.textContent).toContain('Bangalore');
    expect(fixture.nativeElement.textContent).toContain('Bengaluru');
  });
});
