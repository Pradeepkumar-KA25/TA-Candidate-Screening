import { of } from 'rxjs';

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { DuplicateService } from '../../services/duplicate.service';
import { DuplicatesComponent } from './duplicates.component';

describe('DuplicatesComponent', () => {
  let fixture: ComponentFixture<DuplicatesComponent>;
  let duplicateService: jasmine.SpyObj<DuplicateService>;

  beforeEach(async () => {
    duplicateService = jasmine.createSpyObj<DuplicateService>('DuplicateService', ['listGroupedDuplicates'], {
      loading$: of(false),
      error$: of(null),
    });
    duplicateService.markReviewed = jasmine.createSpy().and.returnValue(
      of({
        id: 'd-1',
        match_basis: 'phone',
        confidence: 0.95,
        status: 'reviewed',
        created_at: '2026-08-07T10:30:00Z',
        reviewed_by: 'recruiter-1',
        reviewed_at: '2026-08-07T11:00:00Z',
        candidate: {
          id: '11111111-1111-1111-1111-111111111111',
          zoho_candidate_id: 'z-1',
          full_name: 'Arjun Kumar',
          email: 'arjun@example.com',
          phone: '+919111111111',
          current_company: 'TechNova Solutions',
          current_location: 'Bengaluru',
          total_experience_years: 6,
        },
        matched_candidate: {
          id: '11111111-1111-1111-1111-111111111112',
          zoho_candidate_id: 'z-2',
          full_name: 'Priya Sharma',
          email: 'priya@example.com',
          phone: '+919111111111',
          current_company: 'CloudEdge Systems',
          current_location: 'Bengaluru',
          total_experience_years: 5,
        },
      })
    );
    duplicateService.listGroupedDuplicates.and.returnValue(
      of({
        summary: {
          job_descriptions_reviewed: 2,
          possible_duplicates: 1,
          no_duplicate_signal: 1,
          unassigned_duplicates: 0,
        },
        groups: [
          {
            jd_id: 'jd-1',
            jd_code: 'JD-2026-014',
            jd_title: 'Java Backend Developer',
            duplicate_count: 1,
            items: [
              {
                id: 'd-1',
                match_basis: 'phone',
                confidence: 0.95,
                status: 'pending',
                created_at: '2026-08-07T10:30:00Z',
                candidate: {
                  id: '11111111-1111-1111-1111-111111111111',
                  zoho_candidate_id: 'z-1',
                  full_name: 'Arjun Kumar',
                  email: 'arjun@example.com',
                  phone: '+919111111111',
                  current_company: 'TechNova Solutions',
                  current_location: 'Bengaluru',
                  total_experience_years: 6,
                },
                matched_candidate: {
                  id: '11111111-1111-1111-1111-111111111112',
                  zoho_candidate_id: 'z-2',
                  full_name: 'Priya Sharma',
                  email: 'priya@example.com',
                  phone: '+919111111111',
                  current_company: 'CloudEdge Systems',
                  current_location: 'Bengaluru',
                  total_experience_years: 5,
                },
              },
            ],
          },
          {
            jd_id: 'jd-2',
            jd_code: 'JD-2026-021',
            jd_title: 'Frontend React Developer',
            duplicate_count: 0,
            items: [],
          },
        ],
      })
    );

    await TestBed.configureTestingModule({
      imports: [DuplicatesComponent, RouterTestingModule],
      providers: [{ provide: DuplicateService, useValue: duplicateService }],
    }).compileComponents();

    fixture = TestBed.createComponent(DuplicatesComponent);
    fixture.detectChanges();
  });

  it('should render duplicate groups and candidate comparison cards', () => {
    const html = fixture.nativeElement as HTMLElement;
    expect(html.textContent).toContain('Java Backend Developer');
    expect(html.textContent).toContain('Arjun Kumar');
    expect(html.textContent).toContain('Priya Sharma');
    expect(html.textContent).toContain('No duplicate signals found among candidates filtered for this Job Description.');

    const links = html.querySelectorAll('a.view-btn');
    expect(links.length).toBe(2);
  });

  it('should mark a duplicate as reviewed without reloading the page', () => {
    const html = fixture.nativeElement as HTMLElement;
    const button = html.querySelector('button.review-btn') as HTMLButtonElement;

    button.click();
    fixture.detectChanges();

    expect(duplicateService.markReviewed).toHaveBeenCalledWith('d-1');
    expect(html.textContent).toContain('Reviewed');
  });
});
