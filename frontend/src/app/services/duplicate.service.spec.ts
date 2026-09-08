import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { DuplicateService } from './duplicate.service';
import { ApiConfigService } from '../config/api.config';

describe('DuplicateService', () => {
  let service: DuplicateService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        DuplicateService,
        {
          provide: ApiConfigService,
          useValue: {
            getApiBaseUrl: () => 'http://localhost:8000/api/v1',
          },
        },
      ],
    });

    service = TestBed.inject(DuplicateService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should load grouped duplicates', () => {
    service.listGroupedDuplicates().subscribe((response) => {
      expect(response?.summary.possible_duplicates).toBe(1);
      expect(response?.groups[0].jd_code).toBe('JD-2026-014');
    });

    const request = httpMock.expectOne('http://localhost:8000/api/v1/duplicates');
    expect(request.request.method).toBe('GET');
    request.flush({
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
          items: [],
        },
      ],
    });
  });

  it('should return null when API call fails', () => {
    service.listGroupedDuplicates().subscribe((response) => {
      expect(response).toBeNull();
    });

    const request = httpMock.expectOne('http://localhost:8000/api/v1/duplicates');
    request.flush({ message: 'failed' }, { status: 500, statusText: 'Server Error' });
  });

  it('should mark a duplicate as reviewed', () => {
    service.markReviewed('dup-1').subscribe((response) => {
      expect(response?.status).toBe('reviewed');
      expect(response?.reviewed_by).toBe('r-1');
    });

    const request = httpMock.expectOne('http://localhost:8000/api/v1/duplicates/dup-1/review');
    expect(request.request.method).toBe('PATCH');
    request.flush({
      id: 'dup-1',
      match_basis: 'phone_exact',
      confidence: 0.93,
      status: 'reviewed',
      created_at: '2026-08-07T10:00:00Z',
      reviewed_by: 'r-1',
      reviewed_at: '2026-08-07T11:00:00Z',
      candidate: {
        id: 'c-1',
        zoho_candidate_id: 'z-1',
        full_name: 'Asha Sharma',
        email: 'asha@example.com',
        phone: '+919000000001',
        current_company: null,
        current_location: null,
        total_experience_years: 5,
      },
      matched_candidate: {
        id: 'c-2',
        zoho_candidate_id: 'z-2',
        full_name: 'Asha S',
        email: 'asha.s@example.com',
        phone: '+919000000001',
        current_company: null,
        current_location: null,
        total_experience_years: 5,
      },
    });
  });
});
