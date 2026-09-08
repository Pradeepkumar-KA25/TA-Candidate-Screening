import { CommonModule } from '@angular/common';
import { Component, DestroyRef, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { AuthService } from '../../services/auth.service';

import { SyncSummaryResponse } from '../../models/sync.models';
import { SyncService } from '../../services/sync.service';

@Component({
  selector: 'app-sync-complete',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './sync-complete.component.html',
  styleUrl: './sync-complete.component.css',
})
export class SyncCompleteComponent {
  private readonly destroyRef = inject(DestroyRef);

  syncStatus: SyncSummaryResponse | null = null;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly syncService: SyncService,
    private readonly authService: AuthService,
    private readonly router: Router
  ) {
    const syncId = this.route.snapshot.paramMap.get('syncId');
    if (syncId) {
      this.syncService
        .getSyncSummary(syncId)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe((status) => {
          this.syncStatus = status;
        });
    }
  }

  onLogout(): void {
    this.authService.logoutFromServer().pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.router.navigate(['/login']);
    });
  }

  goBack(): void {
    window.history.back();
  }

  get isSuccessful(): boolean {
    return this.syncStatus?.status === 'completed';
  }
}
