import { CommonModule } from '@angular/common';
import { Component, DestroyRef, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { EMPTY, catchError, switchMap } from 'rxjs';

import { AuthService } from '../../services/auth.service';

import { ZohoIntegrationStatus } from '../../models/integration.models';
import { SyncStatusResponse } from '../../models/sync.models';
import { IntegrationService } from '../../services/integration.service';
import { SyncService } from '../../services/sync.service';

@Component({
  selector: 'app-sync-candidates',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './sync-candidates.component.html',
  styleUrl: './sync-candidates.component.css',
})
export class SyncCandidatesComponent {
  private readonly destroyRef = inject(DestroyRef);

  zohoStatus: ZohoIntegrationStatus | null = null;
  lastSyncStatus: SyncStatusResponse | null = null;
  syncHistory: SyncStatusResponse[] = [];
  showSyncHistory = false;
  syncInProgress = false;
  syncErrorMessage: string | null = null;
  autoSyncToggling = false;

  constructor(
    private readonly router: Router,
    private readonly integrationService: IntegrationService,
    private readonly syncService: SyncService,
    private readonly authService: AuthService
  ) {
    this.integrationService
      .pollZohoStatus()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((status) => {
        this.zohoStatus = status;
      });

    this.syncService.error$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((message) => {
      this.syncErrorMessage = message;
    });

    this.loadSyncHistory();
  }

  onLogout(): void {
    this.authService.logoutFromServer().pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.router.navigate(['/login']);
    });
  }

  goBack(): void {
    window.history.back();
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

  get relativeSyncTime(): string {
    if (!this.zohoStatus?.last_successful_sync_at) {
      return 'Not synced yet';
    }

    const elapsedMs = Date.now() - new Date(this.zohoStatus.last_successful_sync_at).getTime();
    const elapsedDays = Math.floor(elapsedMs / 86_400_000);
    if (elapsedDays > 0) {
      return `Last synced ${elapsedDays} day${elapsedDays === 1 ? '' : 's'} ago`;
    }

    const elapsedHours = Math.floor(elapsedMs / 3_600_000);
    if (elapsedHours > 0) {
      return `Last synced ${elapsedHours} hour${elapsedHours === 1 ? '' : 's'} ago`;
    }

    return 'Last synced recently';
  }

  get nextSyncTime(): string {
    if (!this.zohoStatus?.auto_sync_enabled) {
      return 'Auto-sync is OFF';
    }

    if (!this.zohoStatus?.last_auto_sync_at) {
      return 'Next sync: Soon (first time)';
    }

    const lastSyncTime = new Date(this.zohoStatus.last_auto_sync_at).getTime();
    const intervalMinutes = this.zohoStatus.auto_sync_interval_minutes;
    const nextSyncTime = lastSyncTime + (intervalMinutes * 60 * 1000);
    const now = Date.now();

    if (nextSyncTime <= now) {
      return 'Next sync: Pending (overdue)';
    }

    const remainingMs = nextSyncTime - now;
    const remainingMinutes = Math.ceil(remainingMs / 60_000);

    if (remainingMinutes < 1) {
      return 'Next sync: Within seconds';
    }

    return `Next sync: In ${remainingMinutes} min${remainingMinutes === 1 ? '' : 's'}`;
  }

  get previewSync(): SyncStatusResponse | null {
    return this.syncHistory.find((sync) => sync.status === 'completed') ?? null;
  }

  get stepState(): 'idle' | 'running' | 'completed' {
    if (this.lastSyncStatus?.status === 'completed') {
      return 'completed';
    }
    return this.syncInProgress ? 'running' : 'idle';
  }

  formatLabel(value: string): string {
    return value.replaceAll('_', '-').replace(/\b\w/g, (character) => character.toUpperCase());
  }

  syncDuration(sync: SyncStatusResponse): string {
    if (!sync.completed_at) {
      return 'In progress';
    }
    const seconds = Math.max(0, Math.round((new Date(sync.completed_at).getTime() - new Date(sync.started_at).getTime()) / 1000));
    return seconds < 60 ? `${seconds}s` : `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  }

  toggleSyncHistory(): void {
    this.showSyncHistory = !this.showSyncHistory;
    if (this.showSyncHistory) {
      this.loadSyncHistory();
    }
  }

  toggleAutoSync(): void {
    if (!this.zohoStatus || this.autoSyncToggling) {
      return;
    }

    this.autoSyncToggling = true;
    const newState = !this.zohoStatus.auto_sync_enabled;

    this.integrationService
      .updateAutoSyncSettings({
        auto_sync_enabled: newState,
        auto_sync_interval_minutes: this.zohoStatus.auto_sync_interval_minutes,
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (status) => {
          this.zohoStatus = status;
          this.autoSyncToggling = false;
        },
        error: () => {
          this.syncErrorMessage = 'Failed to update auto-sync settings. Please try again.';
          this.autoSyncToggling = false;
        },
      });
  }

  onStartSync(): void {
    if (!this.isConnected || this.syncInProgress) {
      return;
    }

    this.syncInProgress = true;
    this.syncErrorMessage = null;

    this.syncService
      .startCandidateSync()
      .pipe(
        switchMap((trigger) => {
          if (!trigger.sync_id) {
            this.syncInProgress = false;
            return EMPTY;
          }
          return this.syncService.trackSyncUntilDone(trigger.sync_id);
        }),
        catchError(() => {
          this.syncInProgress = false;
          this.syncErrorMessage = 'Unable to track candidate sync status. Please try again.';
          return EMPTY;
        }),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe((status) => {
        this.lastSyncStatus = status;
        if (status.status === 'running') {
          return;
        }

        this.syncInProgress = false;
        if (status.status === 'completed') {
          this.loadSyncHistory();
          return;
        }

        this.syncErrorMessage = this.syncService.buildFriendlyError(status);
      });
  }

  private loadSyncHistory(): void {
    this.syncService
      .getSyncHistory()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((response) => {
        this.syncHistory = response.items;
      });
  }
}
