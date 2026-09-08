import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ZohoIntegrationStatus } from '../models/integration.models';
import { IntegrationService } from './integration.service';
import { ApiConfigService } from '../config/api.config';

describe('IntegrationService', () => {
  let service: IntegrationService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        IntegrationService,
        {
          provide: ApiConfigService,
          useValue: {
            getApiBaseUrl: () => 'http://localhost:8000/api/v1',
          },
        },
      ],
    });

    service = TestBed.inject(IntegrationService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should fetch Zoho status from backend', () => {
    const response: ZohoIntegrationStatus = {
      integration: 'Zoho Recruit',
      connection_state: 'connected',
      status: 'healthy',
      access_level: 'read_only',
      sync_type: 'manual',
      last_successful_sync_at: '2026-07-28T10:00:00Z',
      last_checked_at: '2026-07-28T10:01:00Z',
    };

    service.getZohoStatus().subscribe((status) => {
      expect(status.connection_state).toBe('connected');
      expect(status.status).toBe('healthy');
    });

    const request = httpMock.expectOne('http://localhost:8000/api/v1/integrations/zoho/status');
    expect(request.request.method).toBe('GET');
    request.flush(response);
  });

  it('should return disconnected fallback when API fails', () => {
    service.getZohoStatus().subscribe((status) => {
      expect(status.connection_state).toBe('disconnected');
      expect(status.status).toBe('disconnected');
    });

    const request = httpMock.expectOne('http://localhost:8000/api/v1/integrations/zoho/status');
    request.flush({ message: 'error' }, { status: 500, statusText: 'Server Error' });
  });
});
