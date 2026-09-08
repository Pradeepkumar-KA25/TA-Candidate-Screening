import { of, throwError } from 'rxjs';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthService } from '../../services/auth.service';
import { LoginComponent } from './login.component';

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let component: LoginComponent;
  let authService: jasmine.SpyObj<AuthService>;
  let router: Router;

  beforeEach(async () => {
    authService = jasmine.createSpyObj<AuthService>('AuthService', ['login']);

    await TestBed.configureTestingModule({
      imports: [LoginComponent, RouterTestingModule],
      providers: [{ provide: AuthService, useValue: authService }],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    spyOn(router, 'navigate').and.resolveTo(true);
    fixture.detectChanges();
  });

  it('should show validation errors when form is submitted empty', () => {
    component.onSubmit();
    fixture.detectChanges();

    expect(component.loginForm.invalid).toBeTrue();
    expect(component.emailControl.touched).toBeTrue();
    expect(component.passwordControl.touched).toBeTrue();
  });

  it('should reject invalid email format', () => {
    component.loginForm.patchValue({
      email: 'invalid-email',
      password: 'Secret123!',
      remember_me: false,
    });

    component.onSubmit();

    expect(component.emailControl.hasError('email')).toBeTrue();
    expect(authService.login).not.toHaveBeenCalled();
  });

  it('should toggle password visibility', () => {
    const passwordInput = fixture.nativeElement.querySelector('#password') as HTMLInputElement;
    const toggleButton = fixture.nativeElement.querySelector('.password-toggle') as HTMLButtonElement;

    expect(passwordInput.type).toBe('password');
    toggleButton.click();
    fixture.detectChanges();

    expect(component.showPassword).toBeTrue();
    expect(passwordInput.type).toBe('text');
    expect(toggleButton.getAttribute('aria-label')).toBe('Hide password');
  });

  it('should submit successfully and navigate to dashboard', () => {
    authService.login.and.returnValue(of({
      token: 'token-value',
      tokenType: 'bearer',
      expiresIn: 3600,
      recruiter: {
        id: '11111111-1111-1111-1111-111111111111',
        full_name: 'Asha Sharma',
        email: 'asha.sharma@example.com',
        role: 'Recruiter',
      },
    }));

    component.loginForm.patchValue({
      email: 'asha.sharma@example.com',
      password: 'Secret123!',
      remember_me: true,
    });

    component.onSubmit();

    expect(authService.login).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
    expect(component.submitError).toBeNull();
  });

  it('should show inline error when login fails', () => {
    authService.login.and.returnValue(
      throwError(() => ({
        error: { message: 'Invalid credentials' },
      }))
    );

    component.loginForm.patchValue({
      email: 'asha.sharma@example.com',
      password: 'WrongPassword',
      remember_me: false,
    });

    component.onSubmit();
    fixture.detectChanges();

    expect(component.submitError).toBe('Invalid credentials');
  });
});
