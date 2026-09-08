import { Component, signal, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { KaniniResumeService } from '../../../services/kanini-resume.service';

@Component({
  selector: 'app-resume-upload',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styleUrls: ['./resume-upload.component.scss'],
  template: `
    <section class="upload" [attr.aria-labelledby]="'upload-title'">
      <header>
        <div>
          <p class="eyebrow">Step 1 of 5</p>
          <h1 id="upload-title">Upload your resume</h1>
          <p class="muted">Supported formats: PDF, Word (.docx, .doc)</p>
        </div>
      </header>

      <div class="model-selector">
        <label for="model-select">
          <span class="label-text">AI Model for Extraction</span>
          <select id="model-select" [(ngModel)]="selectedModel" [disabled]="uploading()">
            <option value="auto">Auto (Recommended)</option>
            <optgroup label="Ollama Models" *ngIf="llmModelsLoaded()">
              <option *ngFor="let model of llmModels()" [value]="model.value">
                {{ model.label }}
              </option>
            </optgroup>
          </select>
        </label>
        <p class="model-hint">Choose an AI model to extract and parse your resume data accurately.</p>
      </div>

      <div class="upload-container">
        <div
          class="dropzone"
          (dragover)="onDragOver($event)"
          (dragleave)="onDragLeave()"
          (drop)="onDrop($event)"
          (click)="fileInput.click()"
          [class.active]="isDragging()"
          [class.has-file]="selectedFile()"
        >
          <input
            type="file"
            #fileInput
            hidden
            accept=".pdf,.docx,.doc"
            (change)="onFileSelect($event)"
          />

          <div *ngIf="!selectedFile()" class="dropzone-content">
            <svg
              class="upload-icon"
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <h2>Drop your resume here</h2>
            <p>or click to browse files</p>
            <p class="hint">PDF, .docx, or .doc files only</p>
          </div>

          <div *ngIf="selectedFile()" class="file-info">
            <svg
              class="file-icon"
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
              <polyline points="13 2 13 9 20 9"></polyline>
            </svg>
            <div class="file-details">
              <strong>{{ selectedFile()?.name }}</strong>
              <p>{{ getFileSizeString() }}</p>
            </div>
            <button
              type="button"
              class="remove-btn"
              (click)="clearFile($event)"
              title="Remove file"
            >
              ✕
            </button>
          </div>
        </div>

        <div *ngIf="error()" class="error-message" role="alert">
          <strong>Error:</strong> {{ error() }}
        </div>

        <div *ngIf="uploading()" class="loading-state">
          <div class="spinner"></div>
          <p>Analyzing your resume...</p>
        </div>
      </div>

      <footer>
        <button
          type="button"
          class="ui-button primary"
          (click)="upload()"
          [disabled]="!selectedFile() || uploading()"
        >
          {{ uploading() ? 'Uploading...' : 'Upload & Continue' }}
        </button>
      </footer>
    </section>
  `,
})
export class ResumeUploadComponent implements OnInit {
  private kaniniService = inject(KaniniResumeService);
  private router = inject(Router);

  selectedFile = signal<File | null>(null);
  isDragging = signal(false);
  uploading = signal(false);
  error = signal('');
  selectedModel = 'auto';
  llmModels = signal<any[]>([]);
  llmModelsLoaded = signal(false);

  ngOnInit(): void {
    this.loadLlmModels();
  }

  private loadLlmModels(): void {
    this.kaniniService.getLlmModels().subscribe({
      next: (response) => {
        const models = response.models || [
          { label: 'Qwen3 32B', value: 'ollama:qwen3:32b', provider: 'ollama', provider_label: 'Ollama' },
          { label: 'Qwen3 14B', value: 'ollama:qwen3:14b', provider: 'ollama', provider_label: 'Ollama' },
          { label: 'Llama 3.3 70B', value: 'ollama:llama3.3:70b', provider: 'ollama', provider_label: 'Ollama' },
          { label: 'Devstral', value: 'ollama:devstral', provider: 'ollama', provider_label: 'Ollama' },
        ];
        this.llmModels.set(models);
        this.llmModelsLoaded.set(true);
      },
      error: () => {
        const defaults = [
          { label: 'Qwen3 32B', value: 'ollama:qwen3:32b', provider: 'ollama', provider_label: 'Ollama' },
          { label: 'Qwen3 14B', value: 'ollama:qwen3:14b', provider: 'ollama', provider_label: 'Ollama' },
          { label: 'Llama 3.3 70B', value: 'ollama:llama3.3:70b', provider: 'ollama', provider_label: 'Ollama' },
          { label: 'Devstral', value: 'ollama:devstral', provider: 'ollama', provider_label: 'Ollama' },
        ];
        this.llmModels.set(defaults);
        this.llmModelsLoaded.set(true);
      },
    });
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(true);
  }

  onDragLeave(): void {
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(false);

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.selectFile(files[0]);
    }
  }

  onFileSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectFile(input.files[0]);
    }
  }

  private selectFile(file: File): void {
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'];
    if (!validTypes.includes(file.type)) {
      this.error.set('Please upload a PDF or Word document.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      this.error.set('File size must be less than 10MB.');
      return;
    }

    this.selectedFile.set(file);
    this.error.set('');
  }

  clearFile(event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    this.selectedFile.set(null);
    this.error.set('');
  }

  getFileSizeString(): string {
    const file = this.selectedFile();
    if (!file) return '';
    const sizeInMb = file.size / (1024 * 1024);
    return sizeInMb < 1 ? `${Math.round(file.size / 1024)} KB` : `${sizeInMb.toFixed(2)} MB`;
  }

  upload(): void {
    const file = this.selectedFile();
    if (!file) {
      this.error.set('Please select a file first.');
      return;
    }

    this.uploading.set(true);
    this.error.set('');

    this.kaniniService.uploadResume(file, this.selectedModel).subscribe({
      next: (response) => {
        this.uploading.set(false);
        console.log('Upload response:', response);
        if (response.resume_id) {
          this.router.navigate(['/resume-generator/review', response.resume_id]);
        } else {
          this.error.set('Invalid response from server. Missing resume_id.');
        }
      },
      error: (err) => {
        this.uploading.set(false);
        console.error('Upload error:', err);
        const errorMsg = err?.error?.detail || err?.error?.message || err?.message || 'Failed to upload resume. Please try again.';
        this.error.set(errorMsg);
      },
    });
  }
}
