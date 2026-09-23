import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  LucideChartNoAxesCombined,
  LucideCopy,
  LucideFileCheck,
  LucideFileText,
  LucideFiles,
  LucideLayout,
  LucideLayoutDashboard,
  LucideListChecks,
  LucideLogOut,
  LucideMoonStar,
  LucidePanelLeftClose,
  LucidePanelLeftOpen,
  LucideSettings,
  LucideSlidersHorizontal,
  LucideSunMedium,
  LucideUsersRound,
} from '@lucide/angular';

import { AppTheme, ThemeService } from '../../services/theme.service';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    LucideChartNoAxesCombined,
    LucideCopy,
    LucideFileCheck,
    LucideFileText,
    LucideFiles,
    LucideLayout,
    LucideLayoutDashboard,
    LucideListChecks,
    LucideLogOut,
    LucideMoonStar,
    LucidePanelLeftClose,
    LucidePanelLeftOpen,
    LucideSettings,
    LucideSlidersHorizontal,
    LucideSunMedium,
    LucideUsersRound,
  ],
  templateUrl: './app-shell.component.html',
  styleUrl: './app-shell.component.css',
})
export class AppShellComponent implements OnInit {
  @Input() activeNav: 'dashboard' | 'candidates' | 'filters' | 'ranking' | 'shortlists' | 'duplicates' | 'settings' | 'resume-generator' | 'my-resumes' | 'create-template' | 'resume-enrichment' = 'dashboard';
  @Input() headerContext = 'Dashboard';
  @Input() statusState: 'connected' | 'disconnected' = 'disconnected';
  @Input() recruiterName = 'Recruiter';
  @Input() recruiterInitials = 'RK';

  @Output() logoutRequested = new EventEmitter<void>();

  sidebarCollapsed = false;
  theme: AppTheme = 'light';

  constructor(private readonly themeService: ThemeService) {}

  ngOnInit(): void {
    this.sidebarCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    this.theme = this.themeService.theme;
  }

  get currentTheme(): AppTheme {
    return this.themeService.theme;
  }

  get logoSrc(): string {
    if (this.sidebarCollapsed) {
      return this.currentTheme === 'dark' ? '/Kanini_logo_darkmode_close.png' : '/Kanini_logo_lightmode_close.png';
    }
    return this.currentTheme === 'dark' ? '/Kanini_logo_darkmode.png' : '/Kanini_logo_lightmode.png';
  }

  toggleSidebar(): void {
    this.sidebarCollapsed = !this.sidebarCollapsed;
    localStorage.setItem('sidebar-collapsed', String(this.sidebarCollapsed));
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
    this.theme = this.themeService.theme;
  }

  onLogout(event: Event): void {
    event.preventDefault();
    this.logoutRequested.emit();
  }
}
