import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AfterViewInit, Component, DestroyRef, ElementRef, OnDestroy, OnInit, ViewChild, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { AuthService } from '../../services/auth.service';
import { DashboardActivityItem, DashboardStats } from '../../models/dashboard.models';
import { DashboardService } from '../../services/dashboard.service';
import { IntegrationService } from '../../services/integration.service';
import { ZohoIntegrationStatus } from '../../models/integration.models';
import { NotificationService } from '../../services/notification.service';
import { DashboardAnalytics } from '../../models/analytics.models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {
  private readonly destroyRef = inject(DestroyRef);

  stats: DashboardStats | null = null;
  recentActivity: DashboardActivityItem[] = [];
  loading = false;
  errorMessage: string | null = null;
  zohoStatus: ZohoIntegrationStatus | null = null;
  analytics: DashboardAnalytics | null = null;
  analyticsDays = 7;
  private charts: Array<{ dispose: () => void }> = [];
  @ViewChild('growthChart') growthChart?: ElementRef<HTMLDivElement>;
  @ViewChild('pipelineChart') pipelineChart?: ElementRef<HTMLDivElement>;
  @ViewChild('sourceChart') sourceChart?: ElementRef<HTMLDivElement>;
  @ViewChild('syncChart') syncChart?: ElementRef<HTMLDivElement>;
  @ViewChild('enrichmentChart') enrichmentChart?: ElementRef<HTMLDivElement>;
  @ViewChild('activityChart') activityChart?: ElementRef<HTMLDivElement>;

  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
    private readonly integrationService: IntegrationService,
    private readonly dashboardService: DashboardService,
    private readonly notificationService: NotificationService,
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
      if (message) this.notificationService.error(message, 'Dashboard unavailable');
    });
  }

  ngOnInit(): void {
    this.loadDashboardOverview(8);
    this.loadAnalytics();
  }

  ngAfterViewInit(): void {
    if (this.analytics) void this.renderCharts();
  }

  ngOnDestroy(): void {
    this.charts.forEach((chart) => chart.dispose());
  }

  loadAnalytics(): void {
    this.dashboardService.getAnalytics(this.analyticsDays).subscribe({
      next: (analytics) => {
        this.analytics = analytics;
        setTimeout(() => void this.renderCharts());
      },
      error: () => this.notificationService.error('Unable to load dashboard analytics.', 'Analytics unavailable'),
    });
  }

  changeAnalyticsRange(days: number): void {
    this.analyticsDays = days;
    this.loadAnalytics();
  }

  private async renderCharts(): Promise<void> {
    if (!this.analytics) return;
    const [echarts, chartTypes, components, renderers] = await Promise.all([
      import('echarts/core'),
      import('echarts/charts'),
      import('echarts/components'),
      import('echarts/renderers'),
    ]);
    echarts.use([
      chartTypes.BarChart,
      chartTypes.LineChart,
      chartTypes.PieChart,
      components.GridComponent,
      components.TooltipComponent,
      renderers.CanvasRenderer,
    ]);
    this.charts.forEach((chart) => chart.dispose());
    this.charts = [];
    if (this.growthChart) {
      const chart = echarts.init(this.growthChart.nativeElement);
      chart.setOption({ tooltip: { trigger: 'axis' }, xAxis: { type: 'category', data: this.analytics.candidate_growth.map((item) => item.label) }, yAxis: { type: 'value' }, series: [{ type: 'line', smooth: true, data: this.analytics.candidate_growth.map((item) => item.value), areaStyle: {} }] });
      this.charts.push(chart);
    }
    if (this.pipelineChart) {
      const chart = echarts.init(this.pipelineChart.nativeElement);
      chart.setOption({ tooltip: {}, xAxis: { type: 'category', data: this.analytics.pipeline.map((item) => item.label) }, yAxis: { type: 'value' }, series: [{ type: 'bar', data: this.analytics.pipeline.map((item) => item.value), itemStyle: { color: '#1d4ed8' } }] });
      this.charts.push(chart);
    }
    if (this.sourceChart) {
      const chart = echarts.init(this.sourceChart.nativeElement);
      chart.setOption({ tooltip: { trigger: 'item' }, series: [{ type: 'pie', radius: ['42%', '72%'], data: this.analytics.sources.map((item) => ({ name: item.label, value: item.value })) }] });
      this.charts.push(chart);
    }
    if (this.syncChart) {
      const chart = echarts.init(this.syncChart.nativeElement);
      chart.setOption({ tooltip: {}, xAxis: { type: 'category', data: this.analytics.sync_outcomes.map((item) => item.label) }, yAxis: { type: 'value' }, series: [{ type: 'bar', data: this.analytics.sync_outcomes.map((item) => item.value), itemStyle: { color: '#0f766e' } }] });
      this.charts.push(chart);
    }
    if (this.enrichmentChart) {
      const chart = echarts.init(this.enrichmentChart.nativeElement);
      chart.setOption({ tooltip: { trigger: 'item' }, series: [{ type: 'pie', radius: ['42%', '72%'], data: this.analytics.enrichment_outcomes.map((item) => ({ name: item.label, value: item.value })) }] });
      this.charts.push(chart);
    }
    if (this.activityChart) {
      const chart = echarts.init(this.activityChart.nativeElement);
      chart.setOption({ tooltip: {}, grid: { left: 120, right: 20 }, xAxis: { type: 'value' }, yAxis: { type: 'category', data: this.analytics.activity_by_action.map((item) => item.label).reverse() }, series: [{ type: 'bar', data: this.analytics.activity_by_action.map((item) => item.value).reverse(), itemStyle: { color: '#b45309' } }] });
      this.charts.push(chart);
    }
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