import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { SavedFilterService } from './saved-filter.service';
import { ApiConfigService } from '../config/api.config';

describe('SavedFilterService', () => {
  let service: SavedFilterService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        SavedFilterService,
        {
          provide: ApiConfigService,
          useValue: {
            getApiBaseUrl: () => 'http://localhost:8000/api/v1',
          },
        },
      ],
    });

    service = TestBed.inject(SavedFilterService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create a saved filter and refresh the list', () => {
    service
      .createSavedFilter({
        name: 'Java Backend Primary',
        jd_id: 'jd-1',
        filter_criteria: { skills: 'Java,Spring Boot' },
      })
      .subscribe((saved) => {
        expect(saved?.name).toBe('Java Backend Primary');
      });

    const postRequest = httpMock.expectOne('http://localhost:8000/api/v1/saved-filters');
    expect(postRequest.request.method).toBe('POST');
    postRequest.flush({
      id: 'sf-1',
      recruiter_id: 'r-1',
      name: 'Java Backend Primary',
      jd_id: 'jd-1',
      filter_criteria: { skills: 'Java,Spring Boot' },
      resolved_query_params: { jd_id: 'jd-1', skills: 'Java,Spring Boot' },
      created_at: '2026-08-04T10:00:00Z',
      updated_at: '2026-08-04T10:00:00Z',
      warning: null,
    });

    const getRequest = httpMock.expectOne('http://localhost:8000/api/v1/saved-filters');
    expect(getRequest.request.method).toBe('GET');
    getRequest.flush([
      {
        id: 'sf-1',
        recruiter_id: 'r-1',
        name: 'Java Backend Primary',
        jd_id: 'jd-1',
        filter_criteria: { skills: 'Java,Spring Boot' },
        resolved_query_params: { jd_id: 'jd-1', skills: 'Java,Spring Boot' },
        created_at: '2026-08-04T10:00:00Z',
        updated_at: '2026-08-04T10:00:00Z',
        warning: null,
      },
    ]);
  });

  it('should load saved filters list', () => {
    service.listSavedFilters().subscribe((items) => {
      expect(items.length).toBe(1);
      expect(items[0].name).toBe('Python JD Focus');
    });

    const request = httpMock.expectOne('http://localhost:8000/api/v1/saved-filters');
    expect(request.request.method).toBe('GET');
    request.flush([
      {
        id: 'sf-2',
        recruiter_id: 'r-1',
        name: 'Python JD Focus',
        jd_id: 'jd-2',
        filter_criteria: { skills: 'Python,FastAPI' },
        resolved_query_params: { jd_id: 'jd-2', skills: 'Python,FastAPI' },
        created_at: '2026-08-04T10:05:00Z',
        updated_at: '2026-08-04T10:05:00Z',
        warning: null,
      },
    ]);
  });
});
