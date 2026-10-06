import { Component, DestroyRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { LucidePalette, LucideRefreshCw, LucideSlidersHorizontal } from '@lucide/angular';

import { AppTheme, ThemeService } from '../../services/theme.service';
import { AuthService } from '../../services/auth.service';
import { IntegrationService } from '../../services/integration.service';
import { ZohoIntegrationStatus } from '../../models/integration.models';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, LucidePalette, LucideRefreshCw, LucideSlidersHorizontal],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.css',
})
export class SettingsComponent {
  private readonly destroyRef = inject(DestroyRef);
  isAdmin = false;
  accessToken = '';
  refreshToken = '';
  credentialsSaving = false;
  credentialsMessage: string | null = null;
  credentialsError: string | null = null;
  zohoStatus: ZohoIntegrationStatus | null = null;

  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
    private readonly themeService: ThemeService,
    private readonly integrationService: IntegrationService
  ) {}

  ngOnInit(): void {
    this.authService.currentUser$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((user) => {
      this.isAdmin = user?.role === 'Admin';
      this.integrationService
        .getZohoStatus()
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe((status) => (this.zohoStatus = status));
    });
  }

  get currentTheme(): AppTheme {
    return this.themeService.theme;
  }

  setTheme(theme: AppTheme): void {
    this.themeService.setTheme(theme);
  }

  get zohoConnectionLabel(): string {
    return this.zohoStatus?.connection_state === 'connected' ? 'Connected' : 'Not Connected';
  }

  get syncStatusLabel(): string {
    return this.zohoStatus?.status ? this.formatLabel(this.zohoStatus.status) : 'Not available';
  }

  get lastSyncLabel(): string {
    if (!this.zohoStatus?.last_successful_sync_at) {
      return 'No successful sync yet';
    }

    return new Date(this.zohoStatus.last_successful_sync_at).toLocaleString();
  }

  private formatLabel(value: string): string {
    return value.replace(/[_-]+/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase());
  }

  saveZohoCredentials(): void {
    if (!this.isAdmin || !this.accessToken.trim() || !this.refreshToken.trim() || this.credentialsSaving) {
      return;
    }

    this.credentialsSaving = true;
    this.credentialsMessage = null;
    this.credentialsError = null;
    this.integrationService
      .saveZohoCredentials({
        access_token: this.accessToken.trim(),
        refresh_token: this.refreshToken.trim(),
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.credentialsSaving = false;
          this.accessToken = '';
          this.refreshToken = '';
          this.credentialsMessage = 'Zoho credentials saved securely.';
        },
        error: () => {
          this.credentialsSaving = false;
          this.credentialsError = 'Unable to save Zoho credentials.';
        },
      });
  }

  onLogout(): void {
    this.authService.logoutFromServer().pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.router.navigate(['/login']);
    });
  }
}