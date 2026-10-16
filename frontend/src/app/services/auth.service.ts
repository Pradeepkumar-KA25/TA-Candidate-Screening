import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, catchError, map, of, tap } from 'rxjs';

import { AuthSession, LoginRequest, LoginResponse, MicrosoftLoginRequest, RecruiterProfile } from '../models/auth.models';
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
        this.persistSession(session, payload.remember_me);
      })
    );
  }

  microsoftLogin(payload: MicrosoftLoginRequest): Observable<AuthSession> {
    return this.httpClient.post<LoginResponse>(`${this.apiBaseUrl}/auth/microsoft-login`, payload).pipe(
      map((response) => ({
        token: response.access_token,
        tokenType: response.token_type,
        expiresIn: response.expires_in,
        recruiter: response.recruiter,
      })),
      tap((session) => {
        this.sessionSubject.next(session);
        this.currentUserSubject.next(session.recruiter);
        this.persistSession(session, payload.remember_me);
      })
    );
  }

  logout(): void {
    this.sessionSubject.next(null);
    this.currentUserSubject.next(null);
    localStorage.removeItem(AUTH_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_STORAGE_KEY);
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

  getCurrentUser(): RecruiterProfile | null {
    return this.currentUserSubject.value;
  }

  isAdmin(): boolean {
    const role = this.getCurrentUser()?.role?.trim().toLowerCase();
    return role === 'admin' || role === 'super admin' || role === 'super_admin';
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
    const serializedLocalSession = localStorage.getItem(AUTH_STORAGE_KEY);
    const serializedSessionStorageSession = sessionStorage.getItem(AUTH_STORAGE_KEY);
    const serializedSession = serializedLocalSession ?? serializedSessionStorageSession;
    if (!serializedSession) {
      return;
    }

    try {
      const session = JSON.parse(serializedSession) as AuthSession;
      if (!session.token || this.isTokenExpired(session.token)) {
        localStorage.removeItem(AUTH_STORAGE_KEY);
        sessionStorage.removeItem(AUTH_STORAGE_KEY);
        return;
      }
      this.sessionSubject.next(session);
      this.currentUserSubject.next(session.recruiter);
    } catch {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      sessionStorage.removeItem(AUTH_STORAGE_KEY);
    }
  }

  private persistSession(session: AuthSession, rememberMe: boolean): void {
    if (rememberMe) {
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
      sessionStorage.removeItem(AUTH_STORAGE_KEY);
      return;
    }

    sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
    localStorage.removeItem(AUTH_STORAGE_KEY);
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