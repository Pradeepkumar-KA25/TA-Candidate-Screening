import { CommonModule } from '@angular/common';
import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { AuthService } from '../../services/auth.service';
import { DashboardActivityItem, DashboardStats } from '../../models/dashboard.models';
import { DashboardService } from '../../services/dashboard.service';
import { IntegrationService } from '../../services/integration.service';
import { ZohoIntegrationStatus } from '../../models/integration.models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  stats: DashboardStats | null = null;
  recentActivity: DashboardActivityItem[] = [];
  loading = false;
  errorMessage: string | null = null;
  zohoStatus: ZohoIntegrationStatus | null = null;

  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
    private readonly integrationService: IntegrationService,
    private readonly dashboardService: DashboardService
  ) {
    this.integrationService
      .pollZohoStatus()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((status) => {
        this.zohoStatus = status;
      });

    this.dashboardService.loading$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((loading) => {
      this.loading = loading;
    });

    this.dashboardService.error$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((message) => {
      this.errorMessage = message;
    });
  }

  ngOnInit(): void {
    this.loadDashboardOverview(8);
  }

  loadDashboardOverview(limit: number): void {
    this.dashboardService
      .loadDashboardOverview(limit)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((overview) => {
        this.stats = overview.stats;
        this.recentActivity = overview.recentActivity;
      });
  }

  activityDescription(item: DashboardActivityItem): string {
    if (item.action_type === 'sync_completed') {
      const newCount = this.activityCount(item.description, 'new');
      const updatedCount = this.activityCount(item.description, 'updated');
      return /(?:new|updated)\s*[=:]\s*\d+/i.test(item.description)
        ? `Sync completed: ${newCount} added, ${updatedCount} updated`
        : 'Candidate sync completed';
    }

    if (item.action_type === 'export_downloaded') {
      const candidateCount = this.activityCount(item.description, 'candidates');
      return candidateCount ? `Exported ${candidateCount} candidates` : 'Exported candidate shortlist';
    }

    return item.description.replace(/\s*\([^)]*(?:bytes|sync_id)[^)]*\)/gi, '').trim();
  }

  candidatePipelineQuery(label: string): Record<string, string> | null {
    const statusByLabel: Record<string, string> = {
      Screening: 'active,screening,open_to_opportunities',
      Interview: 'interview,interview_scheduled',
      Selected: 'selected,hired',
    };
    const status = statusByLabel[label];
    return status ? { status } : null;
  }

  sourceQuery(source: string): Record<string, string> {
    return { source };
  }

  attentionQuery(label: string): Record<string, string> | null {
    return label === 'Candidates waiting for screening'
      ? { status: 'active,screening,open_to_opportunities' }
      : null;
  }

  private activityCount(description: string, key: string): number {
    const match = description.match(new RegExp(`${key}\\s*[=:]\\s*(\\d+)`, 'i'));
    return match ? Number(match[1]) : 0;
  }

  get isConnected(): boolean {
    return this.zohoStatus?.connection_state === 'connected';
  }

  get formattedSyncTime(): string {
    if (!this.zohoStatus?.last_successful_sync_at) {
      return 'Not synced yet';
    }

    return new Date(this.zohoStatus.last_successful_sync_at).toLocaleString();
  }

  get formattedLastSyncAt(): string {
    if (!this.stats?.last_sync_at) {
      return 'Not synced yet';
    }

    return new Date(this.stats.last_sync_at).toLocaleString();
  }

  onLogout(): void {
    this.authService.logoutFromServer().subscribe(() => {
      void this.router.navigate(['/login']);
    });
  }
}