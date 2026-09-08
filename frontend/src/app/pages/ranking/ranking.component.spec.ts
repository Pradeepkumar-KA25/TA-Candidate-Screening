import { of } from 'rxjs';

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { CandidateService } from '../../services/candidate.service';
import { JobDescriptionService } from '../../services/job-description.service';
import { RankingComponent } from './ranking.component';

describe('RankingComponent', () => {
  let fixture: ComponentFixture<RankingComponent>;
  let candidateService: jasmine.SpyObj<CandidateService>;
  let jobDescriptionService: jasmine.SpyObj<JobDescriptionService>;

  beforeEach(async () => {
    candidateService = jasmine.createSpyObj<CandidateService>('CandidateService', ['loadCandidates']);
    jobDescriptionService = jasmine.createSpyObj<JobDescriptionService>('JobDescriptionService', ['listJobDescriptions']);
    jobDescriptionService.listJobDescriptions.and.returnValue(
      of([
        {
          id: 'jd-1',
          jd_code: 'JD-2026-014',
          title: 'Java Backend Developer',
          required_skills: ['Java', 'Spring Boot'],
          created_at: '2026-08-01T10:30:00Z',
        },
      ])
    );
    candidateService.loadCandidates.and.returnValue(
      of({
        items: [
          {
            id: '11111111-1111-1111-1111-111111111111',
            zoho_candidate_id: 'z-1',
            full_name: 'Arjun Kumar',
            skills: ['Java'],
            total_experience_years: 6,
            current_location: 'Bengaluru',
            current_company: 'TechNova Solutions',
            notice_period_days: 30,
            status: 'active',
            match_percentage: 92,
            updated_at: '2026-07-29T10:30:00Z',
          },
        ],
        page: 1,
        page_size: 10,
        total_items: 1,
        total_pages: 1,
        q: null,
        sort_by: 'full_name',
        sort_order: 'asc' as const,
      })
    );

    await TestBed.configureTestingModule({
      imports: [RankingComponent, RouterTestingModule],
      providers: [
        { provide: CandidateService, useValue: candidateService },
        { provide: JobDescriptionService, useValue: jobDescriptionService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(RankingComponent);
    fixture.detectChanges();
  });

  it('should load rankings only after a Job Description is selected', () => {
    expect(candidateService.loadCandidates).not.toHaveBeenCalled();

    const select = fixture.nativeElement.querySelector('select.form-control') as HTMLSelectElement;
    select.value = 'jd-1';
    select.dispatchEvent(new Event('change'));
    fixture.detectChanges();

    const html = fixture.nativeElement as HTMLElement;
    expect(html.textContent).toContain('Arjun Kumar');
    expect(html.textContent).toContain('Java Backend Developer');

    expect(candidateService.loadCandidates).toHaveBeenCalledWith(
      jasmine.objectContaining({ jdId: 'jd-1' })
    );

    const href = html.querySelector('a.view-btn')?.getAttribute('href');
    expect(href).toContain('/candidates/11111111-1111-1111-1111-111111111111');
  });
});
