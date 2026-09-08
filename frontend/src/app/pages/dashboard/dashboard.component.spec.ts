import { of } from 'rxjs';

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthService } from '../../services/auth.service';
import { DashboardService } from '../../services/dashboard.service';
import { IntegrationService } from '../../services/integration.service';
import { DashboardComponent } from './dashboard.component';

describe('DashboardComponent', () => {
  let fixture: ComponentFixture<DashboardComponent>;
  let component: DashboardComponent;
  let authService: jasmine.SpyObj<AuthService>;
  let dashboardService: jasmine.SpyObj<DashboardService>;
  let integrationService: jasmine.SpyObj<IntegrationService>;
  let router: Router;

  beforeEach(async () => {
    authService = jasmine.createSpyObj<AuthService>('AuthService', ['logoutFromServer']);
    dashboardService = jasmine.createSpyObj<DashboardService>('DashboardService', ['loadDashboardOverview'], {
      loading$: of(false),
      error$: of(null),
    });
    integrationService = jasmine.createSpyObj<IntegrationService>('IntegrationService', ['pollZohoStatus']);
    authService.logoutFromServer.and.returnValue(of(undefined));
    dashboardService.loadDashboardOverview.and.returnValue(
      of({
        stats: {
          total_candidates: 2486,
          last_sync_at: '2026-07-28T10:30:00Z',
          current_shortlist_size: 12,
          saved_filter_count: 5,
          new_candidates: 8,
          shortlisted_candidates: 12,
          interview_candidates: 3,
          pending_duplicates: 2,
          last_sync_status: 'completed',
          last_sync_new: 8,
          last_sync_updated: 4,
          last_sync_errors: 0,
          pipeline: [{ label: 'Screening', count: 10 }],
          source_breakdown: [{ label: 'LinkedIn', count: 6 }],
          needs_attention: [{ label: 'Duplicate matches to review', count: 2, route: '/duplicates' }],
        },
        recentActivity: [
          {
            id: '11111111-1111-1111-1111-111111111111',
            actor_id: '22222222-2222-2222-2222-222222222222',
            action_type: 'sync_completed',
            description: 'Zoho candidate sync completed',
            occurred_at: '2026-07-28T10:30:00Z',
          },
        ],
      })
    );
    integrationService.pollZohoStatus.and.returnValue(
      of({
        integration: 'Zoho Recruit',
        connection_state: 'connected',
        status: 'healthy',
        access_level: 'read_only',
        sync_type: 'manual',
        last_successful_sync_at: null,
        last_checked_at: new Date().toISOString(),
      })
    );

    await TestBed.configureTestingModule({
      imports: [DashboardComponent, RouterTestingModule],
      providers: [
        { provide: AuthService, useValue: authService },
        { provide: DashboardService, useValue: dashboardService },
        { provide: IntegrationService, useValue: integrationService },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    spyOn(router, 'navigate').and.resolveTo(true);

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should load dashboard overview data and render the stats', () => {
    expect(dashboardService.loadDashboardOverview).toHaveBeenCalledWith(8);
    const content = fixture.nativeElement.textContent as string;

    expect(content).toContain('New Candidates');
    expect(content).toContain('8');
    expect(content).toContain('12');
    expect(content).toContain('Duplicate matches to review');
    expect(content).toContain('Candidate sync completed');
  });

  it('should call logout service and navigate to login', () => {
    component.onLogout();

    expect(authService.logoutFromServer).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });
});
