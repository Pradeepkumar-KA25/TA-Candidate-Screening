import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { SyncService } from './sync.service';
import { ApiConfigService } from '../config/api.config';

describe('SyncService', () => {
  let service: SyncService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        SyncService,
        {
          provide: ApiConfigService,
          useValue: {
            getApiBaseUrl: () => 'http://localhost:8000/api/v1',
          },
        },
      ],
    });

    service = TestBed.inject(SyncService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should trigger sync and return sync id', () => {
    service.startCandidateSync().subscribe((response) => {
      expect(response.sync_id).toBe('abc-123');
      expect(response.status).toBe('running');
    });

    const request = httpMock.expectOne('http://localhost:8000/api/v1/sync/candidates');
    expect(request.request.method).toBe('POST');
    request.flush({ sync_id: 'abc-123', status: 'running' });
  });

  it('should fetch sync status by id', () => {
    service.getSyncStatus('abc-123').subscribe((status) => {
      expect(status.status).toBe('completed');
      expect(status.records_fetched).toBe(10);
    });

    const request = httpMock.expectOne('http://localhost:8000/api/v1/sync/abc-123');
    expect(request.request.method).toBe('GET');
    request.flush({
      sync_id: 'abc-123',
      status: 'completed',
      started_at: '2026-07-29T10:00:00Z',
      completed_at: '2026-07-29T10:01:00Z',
      records_fetched: 10,
      records_new: 6,
      records_updated: 4,
      error_message: null,
    });
  });

  it('should fetch sync summary by id', () => {
    service.getSyncSummary('abc-123').subscribe((summary) => {
      expect(summary.normalized_records).toBe(3);
      expect(summary.normalization_examples.length).toBe(1);
    });

    const request = httpMock.expectOne('http://localhost:8000/api/v1/sync/abc-123/summary');
    expect(request.request.method).toBe('GET');
    request.flush({
      sync_id: 'abc-123',
      status: 'completed',
      started_at: '2026-07-29T10:00:00Z',
      completed_at: '2026-07-29T10:01:00Z',
      records_fetched: 10,
      records_new: 6,
      records_updated: 4,
      normalized_records: 3,
      normalization_examples: [
        {
          field: 'location',
          raw_value: 'Bangalore',
          normalized_value: 'Bengaluru',
        },
      ],
      error_message: null,
    });
  });
});
