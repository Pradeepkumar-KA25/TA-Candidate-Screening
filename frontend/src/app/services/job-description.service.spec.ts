import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { JobDescriptionService } from './job-description.service';
import { ApiConfigService } from '../config/api.config';

describe('JobDescriptionService', () => {
  let service: JobDescriptionService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        JobDescriptionService,
        {
          provide: ApiConfigService,
          useValue: {
            getApiBaseUrl: () => 'http://localhost:8000/api/v1',
          },
        },
      ],
    });

    service = TestBed.inject(JobDescriptionService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should fetch job descriptions from API', () => {
    service.listJobDescriptions().subscribe((items) => {
      expect(items.length).toBe(1);
      expect(items[0].jd_code).toBe('JD-2026-014');
    });

    const request = httpMock.expectOne('http://localhost:8000/api/v1/job-descriptions');
    expect(request.request.method).toBe('GET');

    request.flush([{ id: 'jd-1', jd_code: 'JD-2026-014', title: 'Java Backend Developer' }]);
  });

  it('should cache job descriptions after first call', () => {
    service.listJobDescriptions().subscribe();

    const request = httpMock.expectOne('http://localhost:8000/api/v1/job-descriptions');
    request.flush([{ id: 'jd-1', jd_code: 'JD-2026-014', title: 'Java Backend Developer' }]);

    service.listJobDescriptions().subscribe((items) => {
      expect(items.length).toBe(1);
    });

    httpMock.expectNone('http://localhost:8000/api/v1/job-descriptions');
  });

  it('should create a JD and refresh job descriptions list', () => {
    service
      .createJobDescription({
        jd_code: 'JD-2026-250',
        title: 'Senior Backend Engineer',
        required_skills: ['Python', 'FastAPI'],
      })
      .subscribe((created) => {
        expect(created?.jd_code).toBe('JD-2026-250');
      });

    const postRequest = httpMock.expectOne('http://localhost:8000/api/v1/job-descriptions');
    expect(postRequest.request.method).toBe('POST');
    postRequest.flush({
      id: 'jd-2',
      jd_code: 'JD-2026-250',
      title: 'Senior Backend Engineer',
      required_skills: ['Python', 'FastAPI'],
      created_at: '2026-08-06T11:00:00Z',
    });

    const listRequest = httpMock.expectOne('http://localhost:8000/api/v1/job-descriptions');
    expect(listRequest.request.method).toBe('GET');
    listRequest.flush([
      { id: 'jd-1', jd_code: 'JD-2026-014', title: 'Java Backend Developer' },
      { id: 'jd-2', jd_code: 'JD-2026-250', title: 'Senior Backend Engineer' },
    ]);
  });
});
