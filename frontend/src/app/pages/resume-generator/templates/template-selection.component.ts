import { Component, OnInit, signal, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { KaniniResumeService } from '../../../services/kanini-resume.service';
import { TemplateMetadata } from '../../../models/resume.model';
import { Subject, takeUntil } from 'rxjs';

@Component({
  selector: 'app-template-selection',
  standalone: true,
  imports: [CommonModule],
  styleUrls: ['./template-selection.component.scss'],
  template: `
    <section class="selection" [attr.aria-labelledby]="'template-title'">
      <header>
        <p class="eyebrow">Step 3 of 5</p>
        <h1 id="template-title">Choose how your resume will look</h1>
        <p>Select a format before moving to preview.</p>
      </header>

      <div *ngIf="loading()" style="text-align: center; padding: 40px;">
        <p>Loading resume templates...</p>
      </div>

      <div *ngIf="!loading()">
        <div *ngIf="error()" class="error-message" role="alert">
          {{ error() }}
        </div>

        <div *ngIf="!error() && templates().length === 0" class="empty-state">
          <p>No templates are available right now.</p>
        </div>

        <div *ngIf="!error() && templates().length > 0" class="cards" role="radiogroup" aria-label="Resume templates">
          <article
            class="card"
            *ngFor="let template of templates(); trackBy: trackByTemplateId"
            [class.selected]="selectedTemplate()?.id === template.id"
          >
            <button
              type="button"
              class="card-select"
              role="radio"
              [attr.aria-checked]="selectedTemplate()?.id === template.id"
              (click)="selectTemplate(template)"
            >
              <span class="page" [class.user-preview]="template.category === 'user'" aria-hidden="true">
                <b></b>
                <i></i>
                <i></i>
                <i></i>
              </span>
              <span>
                <strong>{{ template.name }}</strong>
                <span *ngIf="template.category === 'user'" class="user-template">User-created</span>
                <small>{{ template.description }}</small>
                <em>{{ template.page_size || 'LETTER' }} · {{ template.supported_outputs?.join(' / ') || 'HTML' }}</em>
              </span>
              <span class="state">{{ selectedTemplate()?.id === template.id ? 'Selected' : 'Select' }}</span>
            </button>
          </article>
        </div>
      </div>

      <footer>
        <button type="button" class="ui-button secondary" (click)="goBack()">Back</button>
        <button
          type="button"
          class="ui-button primary"
          (click)="continueToPreview()"
          [disabled]="!selectedTemplate() || loading()"
        >
          Preview
        </button>
      </footer>
    </section>
  `,
})
export class TemplateSelectionComponent implements OnInit, OnDestroy {
  private kaniniService = inject(KaniniResumeService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private destroy$ = new Subject<void>();

  resumeId = '';
  loading = signal(true);
  error = signal('');
  templates = signal<TemplateMetadata[]>([]);
  selectedTemplate = signal<TemplateMetadata | null>(null);

  ngOnInit(): void {
    // Subscribe to route params changes
    this.route.params.pipe(takeUntil(this.destroy$)).subscribe((params) => {
      this.resumeId = params['resumeId'] || '';
      this.loadTemplates();
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadTemplates(): void {
    this.loading.set(true);
    this.error.set('');

    this.kaniniService.listTemplates().subscribe({
      next: (response) => {
        this.loading.set(false);
        if (response.templates && response.templates.length > 0) {
          this.templates.set(response.templates);
          this.selectedTemplate.set(
            response.templates.find((template) => template.category === 'builtin') ?? response.templates[0]
          );
        }
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set('Failed to load templates');
      },
    });
  }

  selectTemplate(template: TemplateMetadata): void {
    this.selectedTemplate.set(template);
  }

  trackByTemplateId(index: number, template: TemplateMetadata): string {
    return template.id;
  }

  goBack(): void {
    this.router.navigate(['/resume-generator/review', this.resumeId]);
  }

  continueToPreview(): void {
    const template = this.selectedTemplate();
    if (template && this.resumeId) {
      this.router.navigate(['/resume-generator/preview', this.resumeId, template.id]);
    }
  }
}
