import { Component, DestroyRef, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { LucidePalette, LucideRefreshCw, LucideSlidersHorizontal } from '@lucide/angular';

import { AppTheme, ThemeService } from '../../services/theme.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [RouterLink, LucidePalette, LucideRefreshCw, LucideSlidersHorizontal],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.css',
})
export class SettingsComponent {
  private readonly destroyRef = inject(DestroyRef);

  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
    private readonly themeService: ThemeService
  ) {}

  get currentTheme(): AppTheme {
    return this.themeService.theme;
  }

  setTheme(theme: AppTheme): void {
    this.themeService.setTheme(theme);
  }

  onLogout(): void {
    this.authService.logoutFromServer().pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.router.navigate(['/login']);
    });
  }
}