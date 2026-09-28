import {
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
} from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, throwError } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
    private readonly notificationService: NotificationService,
  ) {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    const accessToken = this.authService.getAccessToken();
    const requestWithAuth = accessToken
      ? request.clone({
          setHeaders: {
            Authorization: `Bearer ${accessToken}`,
          },
        })
      : request;

    return next.handle(requestWithAuth).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          this.notificationService.warning('Your session has expired. Please sign in again.', 'Session expired');
          this.authService.logout();
          void this.router.navigate(['/login']);
        } else if (error.status !== 0) {
          const detail = typeof error.error?.detail === 'string'
            ? error.error.detail
            : typeof error.error?.message === 'string'
              ? error.error.message
              : 'The request could not be completed. Please try again.';
          this.notificationService.error(detail, `Request failed (${error.status})`);
        }
        return throwError(() => error);
      })
    );
  }
}
