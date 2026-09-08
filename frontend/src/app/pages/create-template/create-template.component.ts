import { Component, ViewChild, ElementRef, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { TemplateService } from '../../services/template.service';
import {
  TemplateDraft,
  GeneratedTemplateDraft,
  Template,
} from '../../models/template.model';

type Step = 'upload' | 'generate' | 'save' | 'success';

@Component({
  selector: 'app-create-template',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './create-template.component.html',
  styleUrl: './create-template.component.css',
})
export class CreateTemplateComponent {
  private readonly templateService = inject(TemplateService);
  readonly router = inject(Router);

  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  readonly currentStep = signal<Step>('upload');
  readonly selectedFile = signal<File | null>(null);
  readonly draftId = signal<string>('');
  readonly generatedDraft = signal<GeneratedTemplateDraft | null>(null);
  readonly templateName = signal<string>('');
  readonly templateDescription = signal<string>('');
  readonly savedTemplate = signal<Template | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');

  constructor() {}

  // ─── Upload Step ───────────────────────────────────────────────────────

  selectFile(file: File): void {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      this.selectedFile.set(null);
      this.error.set('Please select a PDF file');
      return;
    }
    this.selectedFile.set(file);
    this.error.set('');
  }

  onFileInputChange(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) this.selectFile(file);
  }

  browseFiles(): void {
    this.fileInput.nativeElement.click();
  }

  uploadPdf(): void {
    const file = this.selectedFile();
    if (!file) {
      this.error.set('Please select a PDF file to continue');
      return;
    }

    this.loading.set(true);
    this.error.set('');

    this.templateService.uploadSamplePdf(file).subscribe({
      next: (draft: TemplateDraft) => {
        this.draftId.set(draft.draft_id);
        this.loading.set(false);
        this.currentStep.set('generate');
        this.generateTemplate();
      },
      error: (error: any) => {
        this.loading.set(false);
        this.error.set(
          error?.error?.detail || 'Failed to upload PDF. Please try again.'
        );
      },
    });
  }

  // ─── Generate Step ────────────────────────────────────────────────────

  generateTemplate(): void {
    this.loading.set(true);
    this.error.set('');

    this.templateService.generateTemplateDraft(this.draftId()).subscribe({
      next: (draft: GeneratedTemplateDraft) => {
        this.generatedDraft.set(draft);
        this.loading.set(false);
        this.currentStep.set('save');
        
        // Pre-fill name with suggested description if available
        if (draft.suggested_description) {
          this.templateDescription.set(draft.suggested_description);
        }
      },
      error: (error: any) => {
        this.loading.set(false);
        this.error.set(
          error?.error?.detail || 'Failed to generate template. Please try again.'
        );
      },
    });
  }

  // ─── Save Step ────────────────────────────────────────────────────────

  saveTemplate(): void {
    const name = this.templateName();
    if (!name || !name.trim()) {
      this.error.set('Template name is required');
      return;
    }

    this.loading.set(true);
    this.error.set('');

    this.templateService
      .saveTemplateDraft(this.draftId(), name, this.templateDescription())
      .subscribe({
        next: (template: Template) => {
          this.savedTemplate.set(template);
          this.loading.set(false);
          this.currentStep.set('success');
        },
        error: (error: any) => {
          this.loading.set(false);
          this.error.set(
            error?.error?.detail || 'Failed to save template. Please try again.'
          );
        },
      });
  }

  // ─── Navigation ───────────────────────────────────────────────────────

  goBack(): void {
    if (this.currentStep() === 'upload') {
      this.router.navigate(['/dashboard']);
    } else if (this.currentStep() === 'generate') {
      this.currentStep.set('upload');
      this.selectedFile.set(null);
      this.draftId.set('');
    } else if (this.currentStep() === 'save') {
      this.currentStep.set('generate');
    }
  }

  viewAllTemplates(): void {
    this.router.navigate(['/my-resumes']); // Can update with dedicated templates page
  }
}

