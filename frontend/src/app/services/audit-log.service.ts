import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { ApiConfigService } from '../config/api.config';
import { AuditLogResponse } from '../models/audit.models';

@Injectable({ providedIn: 'root' })
export class AuditLogService {
  private readonly apiBaseUrl: string;

  constructor(
    private readonly http: HttpClient,
    private readonly apiConfig: ApiConfigService,
  ) {
    this.apiBaseUrl = this.apiConfig.getApiBaseUrl();
  }

  list(page = 1, pageSize = 25, actionType = '', entityType = '', result = '', actor = '', occurredFrom = '', occurredTo = ''): Observable<AuditLogResponse> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('page_size', pageSize.toString());
    if (actionType) params = params.set('action_type', actionType);
    if (entityType) params = params.set('entity_type', entityType);
    if (result) params = params.set('result', result);
    if (actor) params = params.set('actor', actor);
    if (occurredFrom) params = params.set('occurred_from', `${occurredFrom}T00:00:00Z`);
    if (occurredTo) {
      const inclusiveEnd = new Date(`${occurredTo}T00:00:00Z`);
      inclusiveEnd.setUTCDate(inclusiveEnd.getUTCDate() + 1);
      params = params.set('occurred_to', inclusiveEnd.toISOString());
    }
    return this.http.get<AuditLogResponse>(`${this.apiBaseUrl}/audit-logs`, { params });
  }
}
