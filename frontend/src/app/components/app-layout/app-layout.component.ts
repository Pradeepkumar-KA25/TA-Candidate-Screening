import { Component, DestroyRef, inject } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { AppShellComponent } from '../app-shell/app-shell.component';
import { AuthService } from '../../services/auth.service';
import { IntegrationService } from '../../services/integration.service';

type ActiveNavigation = 'dashboard' | 'candidates' | 'filters' | 'ranking' | 'shortlists' | 'duplicates' | 'settings' | 'resume-generator' | 'my-resumes' | 'create-template' | 'resume-enrichment';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [AppShellComponent, RouterOutlet],
  templateUrl: './app-layout.component.html',
})
export class AppLayoutComponent {
  private readonly destroyRef = inject(DestroyRef);

  activeNav: ActiveNavigation = 'dashboard';
  headerContext = 'Dashboard';
  statusState: 'connected' | 'disconnected' = 'disconnected';

  constructor(
    readonly router: Router,
    private readonly authService: AuthService,
    private readonly integrationService: IntegrationService
  ) {
    this.integrationService
      .pollZohoStatus()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((status) => {
        this.statusState = status.connection_state === 'connected' ? 'connected' : 'disconnected';
      });
  }

  updateRouteContext(url: string): void {
    const cleanUrl = url.split('?')[0];
    if (cleanUrl.startsWith('/candidates/')) {
      this.setRouteContext('candidates', 'Candidate Profile');
    } else if (cleanUrl.startsWith('/candidates')) {
      this.setRouteContext('candidates', 'Candidates');
    } else if (cleanUrl.startsWith('/filters')) {
      this.setRouteContext('filters', 'Filters');
    } else if (cleanUrl.startsWith('/ranking') || cleanUrl.startsWith('/export-success')) {
      this.setRouteContext('ranking', cleanUrl.startsWith('/export-success') ? 'Export Complete' : 'Ranking');
    } else if (cleanUrl.startsWith('/shortlists')) {
      this.setRouteContext('shortlists', 'Shortlists');
    } else if (cleanUrl.startsWith('/duplicates')) {
      this.setRouteContext('duplicates', 'Duplicate Review');
    } else if (cleanUrl.startsWith('/resume-generator')) {
      this.setRouteContext('resume-generator', 'Resume Generator');
    } else if (cleanUrl.startsWith('/my-resumes')) {
      this.setRouteContext('my-resumes', 'My Resumes');
    } else if (cleanUrl.startsWith('/resume-enrichment')) {
      this.setRouteContext('resume-enrichment', 'Resume Enrichment');
    } else if (cleanUrl.startsWith('/create-template')) {
      this.setRouteContext('create-template', 'Create Template');
    } else if (cleanUrl.startsWith('/sync-complete')) {
      this.setRouteContext('settings', 'Settings / Sync Complete');
    } else if (cleanUrl.startsWith('/sync-candidates')) {
      this.setRouteContext('settings', 'Settings / Sync Candidates');
    } else if (cleanUrl.startsWith('/settings')) {
      this.setRouteContext('settings', 'Settings');
    } else {
      this.setRouteContext('dashboard', 'Dashboard');
    }
  }

  onLogout(): void {
    this.authService.logoutFromServer().pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.router.navigate(['/login']);
    });
  }

  private setRouteContext(activeNav: ActiveNavigation, headerContext: string): void {
    this.activeNav = activeNav;
    this.headerContext = headerContext;
  }
}