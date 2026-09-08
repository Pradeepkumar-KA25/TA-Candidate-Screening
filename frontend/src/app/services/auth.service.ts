import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, catchError, map, of, tap } from 'rxjs';

import { AuthSession, LoginRequest, LoginResponse, RecruiterProfile } from '../models/auth.models';
import { ApiConfigService } from '../config/api.config';

const AUTH_STORAGE_KEY = 'ta.auth.session';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private apiBaseUrl: string;
  private readonly sessionSubject = new BehaviorSubject<AuthSession | null>(null);
  private readonly currentUserSubject = new BehaviorSubject<RecruiterProfile | null>(null);

  readonly session$ = this.sessionSubject.asObservable();
  readonly currentUser$ = this.currentUserSubject.asObservable();

  constructor(
    private readonly httpClient: HttpClient,
    private readonly apiConfig: ApiConfigService
  ) {
    this.apiBaseUrl = this.apiConfig.getApiBaseUrl();
    this.restorePersistedSession();
  }

  login(payload: LoginRequest): Observable<AuthSession> {
    return this.httpClient.post<LoginResponse>(`${this.apiBaseUrl}/auth/login`, payload).pipe(
      map((response) => ({
        token: response.access_token,
        tokenType: response.token_type,
        expiresIn: response.expires_in,
        recruiter: response.recruiter,
      })),
      tap((session) => {
        this.sessionSubject.next(session);
        this.currentUserSubject.next(session.recruiter);
        if (payload.remember_me) {
          localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
        } else {
          localStorage.removeItem(AUTH_STORAGE_KEY);
        }
      })
    );
  }

  logout(): void {
    this.sessionSubject.next(null);
    this.currentUserSubject.next(null);
    localStorage.removeItem(AUTH_STORAGE_KEY);
  }

  logoutFromServer(): Observable<void> {
    return this.httpClient.post<{ message: string }>(`${this.apiBaseUrl}/auth/logout`, {}).pipe(
      map(() => undefined),
      catchError(() => of(undefined)),
      tap(() => this.logout())
    );
  }

  getAccessToken(): string | null {
    return this.sessionSubject.value?.token ?? null;
  }

  isAuthenticated(): boolean {
    const token = this.getAccessToken();
    if (!token) {
      return false;
    }

    if (this.isTokenExpired(token)) {
      this.logout();
      return false;
    }

    return true;
  }

  private restorePersistedSession(): void {
    const serializedSession = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!serializedSession) {
      return;
    }

    try {
      const session = JSON.parse(serializedSession) as AuthSession;
      if (!session.token || this.isTokenExpired(session.token)) {
        localStorage.removeItem(AUTH_STORAGE_KEY);
        return;
      }
      this.sessionSubject.next(session);
      this.currentUserSubject.next(session.recruiter);
    } catch {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    }
  }

  private isTokenExpired(token: string): boolean {
    const payload = this.parseJwtPayload(token);
    if (!payload || typeof payload.exp !== 'number') {
      return true;
    }

    return payload.exp * 1000 <= Date.now();
  }

  private parseJwtPayload(token: string): { exp?: number } | null {
    const segments = token.split('.');
    if (segments.length !== 3) {
      return null;
    }

    try {
      const normalizedPayload = segments[1].replace(/-/g, '+').replace(/_/g, '/');
      const decodedPayload = atob(normalizedPayload);
      return JSON.parse(decodedPayload) as { exp?: number };
    } catch {
      return null;
    }
  }
}