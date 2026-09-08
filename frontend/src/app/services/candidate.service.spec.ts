import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { CandidateService } from './candidate.service';
import { ApiConfigService } from '../config/api.config';

describe('CandidateService', () => {
  let service: CandidateService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        CandidateService,
        {
          provide: ApiConfigService,
          useValue: {
            getApiBaseUrl: () => 'http://localhost:8000/api/v1',
          },
        },
      ],
    });

    service = TestBed.inject(CandidateService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should request candidates with search and pagination parameters', () => {
    service.loadCandidates({ q: '  python  ', page: 2, pageSize: 20, sortBy: 'current_company', sortOrder: 'desc' }).subscribe((response) => {
      expect(response.page).toBe(2);
      expect(response.total_items).toBe(1);
    });

    const request = httpMock.expectOne((candidateRequest) => {
      return candidateRequest.url === 'http://localhost:8000/api/v1/candidates';
    });
    expect(request.request.method).toBe('GET');
    expect(request.request.params.get('q')).toBe('python');
    expect(request.request.params.get('page')).toBe('2');
    expect(request.request.params.get('page_size')).toBe('20');
    expect(request.request.params.get('sort_by')).toBe('current_company');
    expect(request.request.params.get('sort_order')).toBe('desc');

    request.flush({
      items: [],
      page: 2,
      page_size: 20,
      total_items: 1,
      total_pages: 1,
      q: 'python',
      sort_by: 'current_company',
      sort_order: 'desc',
    });
  });

  it('should append basic filter parameters to the candidates request', () => {
    service
      .loadCandidates({
        page: 1,
        pageSize: 10,
        sortBy: 'full_name',
        sortOrder: 'asc',
        jdId: 'jd-1',
        skills: ['Java', 'Spring Boot'],
        experienceMin: 4,
        experienceMax: 8,
        location: 'Bengaluru',
        preferredLocation: 'Hyderabad',
        noticePeriodMax: 30,
        status: 'active',
      })
      .subscribe();

    const request = httpMock.expectOne((candidateRequest) => {
      return candidateRequest.url === 'http://localhost:8000/api/v1/candidates';
    });

    expect(request.request.params.get('jd_id')).toBe('jd-1');
    expect(request.request.params.get('skills')).toBe('Java,Spring Boot');
    expect(request.request.params.get('experience_min')).toBe('4');
    expect(request.request.params.get('experience_max')).toBe('8');
    expect(request.request.params.get('location')).toBe('Bengaluru');
    expect(request.request.params.get('preferred_location')).toBe('Hyderabad');
    expect(request.request.params.get('notice_period_max')).toBe('30');
    expect(request.request.params.get('status')).toBe('active');

    request.flush({
      items: [],
      page: 1,
      page_size: 10,
      total_items: 0,
      total_pages: 1,
      q: null,
      sort_by: 'full_name',
      sort_order: 'asc',
    });
  });

  it('should append advanced filter parameters to the candidates request', () => {
    service
      .loadCandidates({
        page: 1,
        pageSize: 10,
        sortBy: 'full_name',
        sortOrder: 'asc',
        degree: 'Bachelor',
        certification: 'AWS',
        resumeUpdatedSince: 30,
        source: 'zoho_recruit',
        relevantExperience: 4,
        currentCtc: 10,
        expectedCtc: 14,
        previousCompany: 'Infosys',
        employmentStatus: 'employed',
      })
      .subscribe();

    const request = httpMock.expectOne((candidateRequest) => {
      return candidateRequest.url === 'http://localhost:8000/api/v1/candidates';
    });

    expect(request.request.params.get('degree')).toBe('Bachelor');
    expect(request.request.params.get('certification')).toBe('AWS');
    expect(request.request.params.get('resume_updated_since')).toBe('30');
    expect(request.request.params.get('source')).toBe('zoho_recruit');
    expect(request.request.params.get('relevant_experience')).toBe('4');
    expect(request.request.params.get('current_ctc')).toBe('10');
    expect(request.request.params.get('expected_ctc')).toBe('14');
    expect(request.request.params.get('previous_company')).toBe('Infosys');
    expect(request.request.params.get('employment_status')).toBe('employed');

    request.flush({
      items: [],
      page: 1,
      page_size: 10,
      total_items: 0,
      total_pages: 1,
      q: null,
      sort_by: 'full_name',
      sort_order: 'asc',
    });
  });

  it('should return an empty fallback when the candidate API fails', () => {
    service.loadCandidates({ page: 1, pageSize: 10, sortBy: 'full_name', sortOrder: 'asc' }).subscribe((response) => {
      expect(response.items).toEqual([]);
      expect(response.total_items).toBe(0);
      expect(response.total_pages).toBe(1);
    });

    const request = httpMock.expectOne('http://localhost:8000/api/v1/candidates?page=1&page_size=10&sort_by=full_name&sort_order=asc');
    request.flush({ message: 'error' }, { status: 500, statusText: 'Server Error' });
  });
});
