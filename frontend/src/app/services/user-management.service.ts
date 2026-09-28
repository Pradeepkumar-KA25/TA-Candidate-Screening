import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { ApiConfigService } from '../config/api.config';
import { CreateUserRequest, ManagedUser } from '../models/user.models';

@Injectable({ providedIn: 'root' })
export class UserManagementService {
  private readonly apiBaseUrl: string;

  constructor(private readonly http: HttpClient, apiConfig: ApiConfigService) {
    this.apiBaseUrl = apiConfig.getApiBaseUrl();
  }

  list(): Observable<ManagedUser[]> {
    return this.http.get<ManagedUser[]>(`${this.apiBaseUrl}/users`);
  }

  create(request: CreateUserRequest): Observable<ManagedUser> {
    return this.http.post<ManagedUser>(`${this.apiBaseUrl}/users`, request);
  }

  update(userId: string, payload: Partial<Pick<ManagedUser, 'full_name' | 'role' | 'is_active'>>): Observable<ManagedUser> {
    return this.http.patch<ManagedUser>(`${this.apiBaseUrl}/users/${userId}`, payload);
  }

  resetPassword(userId: string, password: string): Observable<void> {
    return this.http.post<void>(`${this.apiBaseUrl}/users/${userId}/reset-password`, { password });
  }
}
