import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { DashboardService } from './dashboard.service';
import { ApiConfigService } from '../config/api.config';

describe('DashboardService', () => {
  let service: DashboardService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        DashboardService,
        {
          provide: ApiConfigService,
          useValue: {
            getApiBaseUrl: () => 'http://localhost:8000/api/v1',
          },
        },
      ],
    });

    service = TestBed.inject(DashboardService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should fetch dashboard stats and recent activity together', () => {
    service.loadDashboardOverview(2).subscribe((overview) => {
      expect(overview.stats.total_candidates).toBe(42);
      expect(overview.recentActivity.length).toBe(1);
    });

    const statsRequest = httpMock.expectOne('http://localhost:8000/api/v1/dashboard/stats');
    expect(statsRequest.request.method).toBe('GET');
    statsRequest.flush({
      total_candidates: 42,
      last_sync_at: '2026-07-28T10:30:00Z',
      current_shortlist_size: 7,
      saved_filter_count: 3,
    });

    const activityRequest = httpMock.expectOne((request) => {
      return request.url === 'http://localhost:8000/api/v1/dashboard/recent-activity' && request.params.get('limit') === '2';
    });
    expect(activityRequest.request.method).toBe('GET');
    activityRequest.flush({
      items: [
        {
          id: '11111111-1111-1111-1111-111111111111',
          actor_id: '22222222-2222-2222-2222-222222222222',
          action_type: 'sync_completed',
          description: 'Zoho candidate sync completed',
          occurred_at: '2026-07-28T10:30:00Z',
        },
      ],
    });
  });

  it('should return fallback dashboard stats when the stats endpoint fails', () => {
    service.getDashboardStats().subscribe((stats) => {
      expect(stats.total_candidates).toBe(0);
      expect(stats.current_shortlist_size).toBe(0);
      expect(stats.saved_filter_count).toBe(0);
      expect(stats.last_sync_at).toBeNull();
    });

    const request = httpMock.expectOne('http://localhost:8000/api/v1/dashboard/stats');
    request.flush({ message: 'error' }, { status: 500, statusText: 'Server Error' });
  });
});
