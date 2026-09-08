import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, DestroyRef } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { AuthService } from '../../services/auth.service';

interface ExportMetadata {
  filename: string;
  candidate_count: number;
  jd_title: string;
  generated_at: string;
}

@Component({
  selector: 'app-export-success',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './export-success.component.html',
  styleUrl: './export-success.component.css',
})
export class ExportSuccessComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  metadata: ExportMetadata | null = null;
  loading = false;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly authService: AuthService
  ) {}

  ngOnInit(): void {
    // Get metadata from route state
    const navigation = this.router.getCurrentNavigation();
    if (navigation?.extras?.state && navigation.extras.state['metadata']) {
      this.metadata = navigation.extras.state['metadata'];
    }

    // If no metadata, check query params as fallback
    if (!this.metadata) {
      this.route.queryParams.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
        if (params['filename']) {
          this.metadata = {
            filename: params['filename'],
            candidate_count: parseInt(params['candidate_count'], 10) || 0,
            jd_title: params['jd_title'] || 'Unknown',
            generated_at: params['generated_at'] || new Date().toISOString(),
          };
        }
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

  downloadAgain(): void {
    if (this.metadata) {
      // Navigate back to ranking with download intent
      this.router.navigate(['/ranking'], {
        queryParams: { download: 'true' },
      });
    }
  }

  backToRanking(): void {
    this.router.navigate(['/ranking']);
  }

  backToCandidates(): void {
    this.router.navigate(['/candidates']);
  }
}
