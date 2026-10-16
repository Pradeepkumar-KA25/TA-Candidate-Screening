import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  private readonly formBuilder = inject(FormBuilder);
  private readonly microsoftClientId = environment.microsoftClientId;
  private readonly microsoftTenantId = environment.microsoftTenantId || 'organizations';

  isSubmitting = false;
  showPassword = false;
  submitError: string | null = null;

  readonly loginForm = this.formBuilder.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
    remember_me: [false],
  });

  constructor(
    private readonly authService: AuthService,
    private readonly router: Router
  ) {}

  get emailControl() {
    return this.loginForm.controls.email;
  }

  get passwordControl() {
    return this.loginForm.controls.password;
  }

  togglePasswordVisibility(): void {
    this.showPassword = !this.showPassword;
  }

  onSubmit(): void {
    this.submitError = null;
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    const payload = this.loginForm.getRawValue();
    this.isSubmitting = true;
    this.authService.login(payload).subscribe({
      next: () => {
        this.isSubmitting = false;
        void this.router.navigate(['/dashboard']);
      },
      error: (error: { error?: { message?: string } }) => {
        this.isSubmitting = false;
        this.submitError =
          error.error?.message ??
          'Invalid email/username or password. Please check your credentials and try again.';
      },
    });
  }

  async onMicrosoftSignIn(): Promise<void> {
    this.submitError = null;

    if (!this.microsoftClientId) {
      this.submitError = 'Microsoft sign-in is not configured. Contact your administrator.';
      return;
    }

    this.isSubmitting = true;
    try {
      const { PublicClientApplication } = await import('@azure/msal-browser');
      const msalClient = new PublicClientApplication({
        auth: {
          clientId: this.microsoftClientId,
          authority: `https://login.microsoftonline.com/${this.microsoftTenantId}`,
          redirectUri: window.location.origin,
        },
        cache: {
          cacheLocation: 'sessionStorage',
        },
      });
      await msalClient.initialize();

      const loginResponse = await msalClient.loginPopup({
        scopes: ['openid', 'profile', 'email'],
      });

      if (!loginResponse.idToken) {
        throw new Error('Missing Microsoft ID token');
      }

      await firstValueFrom(
        this.authService.microsoftLogin({
          id_token: loginResponse.idToken,
          remember_me: this.loginForm.controls.remember_me.value,
        })
      );

      this.isSubmitting = false;
      await this.router.navigate(['/dashboard']);
    } catch (error) {
      this.isSubmitting = false;
      const message = (error as { error?: { message?: string }; message?: string })?.error?.message;
      this.submitError =
        message ??
        'Microsoft sign-in failed. Please use your @kanini.com account and try again.';
    }
  }
}
