import { of } from 'rxjs';

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthService } from '../../services/auth.service';
import { IntegrationService } from '../../services/integration.service';
import { SyncService } from '../../services/sync.service';
import { SyncCandidatesComponent } from './sync-candidates.component';

describe('SyncCandidatesComponent', () => {
  let fixture: ComponentFixture<SyncCandidatesComponent>;
  let component: SyncCandidatesComponent;
  let integrationService: jasmine.SpyObj<IntegrationService>;
  let syncService: jasmine.SpyObj<SyncService>;
  let authService: jasmine.SpyObj<AuthService>;

  beforeEach(async () => {
    integrationService = jasmine.createSpyObj<IntegrationService>('IntegrationService', ['pollZohoStatus']);
    authService = jasmine.createSpyObj<AuthService>('AuthService', ['logoutFromServer']);
    syncService = jasmine.createSpyObj<SyncService>('SyncService', [
      'startCandidateSync',
      'trackSyncUntilDone',
      'buildFriendlyError',
      'getSyncHistory',
    ]);

    Object.defineProperty(syncService, 'error$', {
      get: () => of(null),
    });

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

    syncService.startCandidateSync.and.returnValue(of({ sync_id: 'sync-1', status: 'running' }));
    syncService.getSyncHistory.and.returnValue(of({ items: [] }));
    syncService.trackSyncUntilDone.and.returnValue(
      of({
        sync_id: 'sync-1',
        status: 'completed',
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        records_fetched: 1,
        records_new: 1,
        records_updated: 0,
        records_failed: 0,
        duplicate_matches: 0,
        error_message: null,
      })
    );

    await TestBed.configureTestingModule({
      imports: [SyncCandidatesComponent, RouterTestingModule],
      providers: [
        { provide: IntegrationService, useValue: integrationService },
        { provide: SyncService, useValue: syncService },
        { provide: AuthService, useValue: authService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SyncCandidatesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should render sync overview steps', () => {
    const element = fixture.nativeElement as HTMLElement;
    expect(element.textContent).toContain('Sync Overview');
    expect(element.textContent).toContain('Fetched');
    expect(element.textContent).toContain('Sync Result Preview');
  });

  it('should start sync when button is clicked', () => {
    component.onStartSync();

    expect(syncService.startCandidateSync).toHaveBeenCalled();
    expect(syncService.trackSyncUntilDone).toHaveBeenCalledWith('sync-1');
  });
});
