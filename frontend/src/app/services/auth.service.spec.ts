import { HttpClient } from '@angular/common/http';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { skip } from 'rxjs/operators';

import { LoginResponse } from '../models/auth.models';
import { AuthService } from './auth.service';
import { ApiConfigService } from '../config/api.config';

function createJwt(expirationSecondsFromNow: number): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(
    JSON.stringify({
      sub: '11111111-1111-1111-1111-111111111111',
      role: 'Recruiter',
      exp: Math.floor(Date.now() / 1000) + expirationSecondsFromNow,
    })
  );

  return `${header}.${payload}.signature`;
}

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        AuthService,
        {
          provide: ApiConfigService,
          useValue: {
            getApiBaseUrl: () => 'http://localhost:8000/api/v1',
          },
        },
      ],
    });

    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should persist session in localStorage when remember_me is true', () => {
    const mockResponse: LoginResponse = {
      access_token: 'token-value',
      token_type: 'bearer',
      expires_in: 3600,
      recruiter: {
        id: '11111111-1111-1111-1111-111111111111',
        full_name: 'Asha Sharma',
        email: 'asha.sharma@example.com',
        role: 'Recruiter',
      },
    };

    service.login({ email: 'asha.sharma@example.com', password: 'Secret123!', remember_me: true }).subscribe();

    const request = httpMock.expectOne('http://localhost:8000/api/v1/auth/login');
    expect(request.request.method).toBe('POST');
    request.flush(mockResponse);

    const session = JSON.parse(localStorage.getItem('ta.auth.session') ?? '{}') as { token: string };
    expect(session.token).toBe('token-value');
  });

  it('should avoid persisting session when remember_me is false', () => {
    const mockResponse: LoginResponse = {
      access_token: 'token-value',
      token_type: 'bearer',
      expires_in: 3600,
      recruiter: {
        id: '11111111-1111-1111-1111-111111111111',
        full_name: 'Asha Sharma',
        email: 'asha.sharma@example.com',
        role: 'Recruiter',
      },
    };

    service.login({ email: 'asha.sharma@example.com', password: 'Secret123!', remember_me: false }).subscribe();

    const request = httpMock.expectOne('http://localhost:8000/api/v1/auth/login');
    request.flush(mockResponse);

    expect(localStorage.getItem('ta.auth.session')).toBeNull();
  });

  it('should expose current recruiter in currentUser$ after successful login', async () => {
    const mockResponse: LoginResponse = {
      access_token: 'token-value',
      token_type: 'bearer',
      expires_in: 3600,
      recruiter: {
        id: '11111111-1111-1111-1111-111111111111',
        full_name: 'Asha Sharma',
        email: 'asha.sharma@example.com',
        role: 'Recruiter',
      },
    };

    const userPromise = firstValueFrom(service.currentUser$.pipe(skip(1)));

    service.login({ email: 'asha.sharma@example.com', password: 'Secret123!', remember_me: false }).subscribe();
    const request = httpMock.expectOne('http://localhost:8000/api/v1/auth/login');
    request.flush(mockResponse);

    const currentUser = await userPromise;
    expect(currentUser?.email).toBe('asha.sharma@example.com');
  });

  it('should return true from isAuthenticated when token is present and not expired', () => {
    const activeToken = createJwt(600);
    localStorage.setItem(
      'ta.auth.session',
      JSON.stringify({
        token: activeToken,
        tokenType: 'bearer',
        expiresIn: 3600,
        recruiter: {
          id: '11111111-1111-1111-1111-111111111111',
          full_name: 'Asha Sharma',
          email: 'asha.sharma@example.com',
          role: 'Recruiter',
        },
      })
    );

    const apiConfig = TestBed.inject(ApiConfigService);
    const freshService = new AuthService(TestBed.inject(HttpClient), apiConfig);
    expect(freshService.isAuthenticated()).toBeTrue();
    expect(freshService.getAccessToken()).toBe(activeToken);
  });

  it('should clear persisted session when token is expired', () => {
    const expiredToken = createJwt(-60);
    localStorage.setItem(
      'ta.auth.session',
      JSON.stringify({
        token: expiredToken,
        tokenType: 'bearer',
        expiresIn: 3600,
        recruiter: {
          id: '11111111-1111-1111-1111-111111111111',
          full_name: 'Asha Sharma',
          email: 'asha.sharma@example.com',
          role: 'Recruiter',
        },
      })
    );

    const apiConfig = TestBed.inject(ApiConfigService);
    const freshService = new AuthService(TestBed.inject(HttpClient), apiConfig);
    expect(freshService.isAuthenticated()).toBeFalse();
    expect(freshService.getAccessToken()).toBeNull();
    expect(localStorage.getItem('ta.auth.session')).toBeNull();
  });

  it('should call backend logout and clear local session', async () => {
    const activeToken = createJwt(600);
    localStorage.setItem(
      'ta.auth.session',
      JSON.stringify({
        token: activeToken,
        tokenType: 'bearer',
        expiresIn: 3600,
        recruiter: {
          id: '11111111-1111-1111-1111-111111111111',
          full_name: 'Asha Sharma',
          email: 'asha.sharma@example.com',
          role: 'Recruiter',
        },
      })
    );

    service = TestBed.inject(AuthService);
    const logoutPromise = firstValueFrom(service.logoutFromServer());

    const request = httpMock.expectOne('http://localhost:8000/api/v1/auth/logout');
    expect(request.request.method).toBe('POST');
    request.flush({ message: 'Logout successful' });

    await logoutPromise;
    expect(localStorage.getItem('ta.auth.session')).toBeNull();
    expect(service.getAccessToken()).toBeNull();
  });
});