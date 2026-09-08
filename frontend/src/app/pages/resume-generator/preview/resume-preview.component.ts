import { Component, OnInit, OnDestroy, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { KaniniResumeService } from '../../../services/kanini-resume.service';
import { Subject, takeUntil, timeout } from 'rxjs';

@Component({
  selector: 'app-resume-preview',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './resume-preview.component.html',
  styleUrls: ['./resume-preview.component.scss'],
})
export class ResumePreviewComponent implements OnInit, OnDestroy {
  private kaniniService = inject(KaniniResumeService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private sanitizer = inject(DomSanitizer);
  private destroy$ = new Subject<void>();

  // State management with signals (Kanini-style)
  readonly loading = signal(true);
  readonly error = signal('');
  readonly previewHtml = signal<SafeHtml>('');
  readonly downloading = signal(false);
  readonly showDownloadMenu = signal(false);

  // Component properties
  resumeId = '';
  templateId = '';
  templateName = '';

  ngOnInit(): void {
    // Subscribe to route params changes - whenever resumeId or templateId changes, reload
    this.route.params.pipe(takeUntil(this.destroy$)).subscribe((params) => {
      this.resumeId = params['resumeId'] || '';
      this.templateId = params['templateId'] || '';

      // Set template name for display
      this.templateName = this.templateId
        ? `Template: ${this.templateId.replace(/[_-]/g, ' ')}`
        : 'Template';

      // Load preview when params change
      if (this.resumeId && this.templateId) {
        this.loadPreview();
      } else {
        this.error.set('Missing resume or template ID');
        this.loading.set(false);
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load the preview from the backend
   * This calls the preview endpoint which returns HTML
   */
  loadPreview(): void {
    if (!this.resumeId || !this.templateId) {
      this.error.set('Missing resume or template ID');
      this.loading.set(false);
      return;
    }

    this.loading.set(true);
    this.error.set('');
    this.previewHtml.set('');

    // Call backend to get preview HTML
    this.kaniniService
      .getPreviewHtml(this.resumeId, this.templateId)
      .pipe(
        timeout(30000), // 30-second timeout
        takeUntil(this.destroy$)
      )
      .subscribe({
        next: (response: any) => {
          try {
            // Extract HTML from response - check both fields for compatibility
            const htmlContent = response?.html || response?.preview_html || '';

            if (!htmlContent || htmlContent.trim().length === 0) {
              this.error.set('No preview content available. Please ensure your resume has data.');
              this.loading.set(false);
              return;
            }

            // Sanitize and set HTML for display
            this.previewHtml.set(
              this.sanitizer.bypassSecurityTrustHtml(htmlContent)
            );
            this.loading.set(false);
          } catch (parseError) {
            console.error('Preview parse error:', parseError);
            this.error.set('Failed to parse preview data');
            this.loading.set(false);
          }
        },
        error: (err) => {
          console.error('Preview load error:', err);
          let errorMsg = 'We couldn\'t generate the preview. Please try again.';

          // Provide specific error messages based on HTTP status
          if (err?.status === 401) {
            errorMsg = 'Session expired. Please login again.';
          } else if (err?.status === 404) {
            errorMsg = 'Resume or template not found.';
          } else if (err?.status === 403) {
            errorMsg = 'Access denied.';
          } else if (err?.name === 'TimeoutError') {
            errorMsg = 'Preview request timed out. Please try again.';
          }

          this.error.set(errorMsg);
          this.loading.set(false);
        },
      });
  }

  /**
   * Navigate back to template selection to change template
   */
  changeTemplate(): void {
    this.router.navigate(['/resume-generator/templates', this.resumeId]);
  }

  /**
   * Show download options menu
   */
  showDownloadOptions(): void {
    this.showDownloadMenu.set(true);
  }

  /**
   * Close download options menu
   */
  closeDownloadOptions(): void {
    this.showDownloadMenu.set(false);
  }

  /** Download a rendered resume without persisting it on the backend. */
  downloadAs(format: 'html' | 'docx' | 'pdf'): void {
    if (this.downloading() || !this.resumeId || !this.templateId) {
      return;
    }

    this.downloading.set(true);
    this.closeDownloadOptions();

    // The render endpoint returns the file bytes directly.
    this.kaniniService
      .renderResume(this.resumeId, this.templateId, format)
      .pipe(
        timeout(30000),
        takeUntil(this.destroy$)
      )
      .subscribe({
        next: (response) => {
          const blob = response.body;
          if (!blob) {
            this.downloading.set(false);
            this.error.set('Failed to generate resume file');
            return;
          }

          const disposition = response.headers.get('content-disposition') || '';
          const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || `Resume.${format}`;
          this.downloading.set(false);
          this.triggerDownload(blob, filename);
        },
        error: (renderErr) => {
          this.downloading.set(false);
          console.error('Render error:', renderErr);
          this.error.set('Failed to generate resume. Please try again.');
        },
      });
  }

  /**
   * Trigger browser download with the given blob and filename
   */
  private triggerDownload(blob: Blob, filename: string = 'resume'): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;  // Set the download filename
    link.click();
    window.URL.revokeObjectURL(url);
  }
}
