import { HTTP_INTERCEPTORS, HttpClient } from '@angular/common/http';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';
import { AuthInterceptor } from './auth.interceptor';

describe('AuthInterceptor', () => {
  let httpClient: HttpClient;
  let httpMock: HttpTestingController;
  let authService: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;
  let notificationService: jasmine.SpyObj<NotificationService>;

  beforeEach(() => {
    authService = jasmine.createSpyObj<AuthService>('AuthService', ['getAccessToken', 'logout']);
    router = jasmine.createSpyObj<Router>('Router', ['navigate']);
    notificationService = jasmine.createSpyObj<NotificationService>('NotificationService', ['warning', 'error']);
    router.navigate.and.resolveTo(true);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        { provide: AuthService, useValue: authService },
        { provide: Router, useValue: router },
        { provide: NotificationService, useValue: notificationService },
        {
          provide: HTTP_INTERCEPTORS,
          useClass: AuthInterceptor,
          multi: true,
        },
      ],
    });

    httpClient = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should append bearer token when available', () => {
    authService.getAccessToken.and.returnValue('jwt-token');

    httpClient.get('/api/test').subscribe();

    const request = httpMock.expectOne('/api/test');
    expect(request.request.headers.get('Authorization')).toBe('Bearer jwt-token');
    request.flush({});
  });

  it('should clear session and redirect on 401 responses', () => {
    authService.getAccessToken.and.returnValue('jwt-token');

    httpClient.get('/api/test').subscribe({
      error: () => {
        // Expected error path for 401 response.
      },
    });

    const request = httpMock.expectOne('/api/test');
    request.flush({ message: 'Unauthorized' }, { status: 401, statusText: 'Unauthorized' });

    expect(authService.logout).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
    expect(notificationService.warning).toHaveBeenCalled();
  });

  it('should not force logout on login endpoint 401 responses', () => {
    authService.getAccessToken.and.returnValue(null);

    httpClient.post('/api/v1/auth/login', { email: 'user@kanini.com', password: 'x' }).subscribe({
      error: () => {
        // Expected error path for 401 response.
      },
    });

    const request = httpMock.expectOne('/api/v1/auth/login');
    request.flush({ message: 'Invalid credentials' }, { status: 401, statusText: 'Unauthorized' });

    expect(authService.logout).not.toHaveBeenCalled();
    expect(router.navigate).not.toHaveBeenCalled();
    expect(notificationService.warning).not.toHaveBeenCalled();
  });
});
