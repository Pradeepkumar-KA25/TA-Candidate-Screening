import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FieldGroup } from '../../services/candidate-fields.service';
import { CandidateFieldItemComponent } from '../candidate-field-item/candidate-field-item.component';

@Component({
  selector: 'app-candidate-field-section',
  standalone: true,
  imports: [CommonModule, CandidateFieldItemComponent],
  template: `
    <div class="section-container">
      <button class="section-header" (click)="toggleSection()">
        <span class="section-icon" [class.expanded]="section.expanded">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </span>
        <span class="section-title">{{ section.description }}</span>
        <span class="section-count">{{ section.fields.length }} fields</span>
      </button>

      <div class="section-content" *ngIf="section.expanded">
        <div class="fields-container">
          <app-candidate-field-item 
            *ngFor="let field of section.fields" 
            [field]="field">
          </app-candidate-field-item>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .section-container {
      margin-bottom: 16px;
      background: var(--surface);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      overflow: hidden;
      transition: background-color 0.2s ease, border-color 0.2s ease;
    }

    .section-header {
      width: 100%;
      padding: 14px 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      background: var(--surface-strong);
      border: none;
      cursor: pointer;
      transition: background-color 0.2s;
      font-size: 1rem;
      font-weight: 600;
      color: var(--text-primary);
      text-align: left;
    }

    .section-header:hover {
      background: var(--surface-alt);
    }

    .section-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s;
      color: var(--text-secondary);
    }

    .section-icon.expanded {
      transform: rotate(180deg);
    }

    .section-title {
      flex: 1;
    }

    .section-count {
      font-size: 0.875rem;
      color: var(--text-muted);
      background: var(--surface);
      padding: 2px 8px;
      border-radius: 12px;
    }

    .section-content {
      max-height: 2000px;
      overflow: hidden;
      animation: slideDown 0.3s ease-out;
    }

    @keyframes slideDown {
      from {
        max-height: 0;
        opacity: 0;
      }
      to {
        max-height: 2000px;
        opacity: 1;
      }
    }

    .fields-container {
      padding: 16px;
    }

    @media (max-width: 768px) {
      .section-header {
        padding: 12px 14px;
        font-size: 0.95rem;
      }

      .section-count {
        font-size: 0.75rem;
      }
    }
  `]
})
export class CandidateFieldSectionComponent {
  @Input() section!: FieldGroup;
  @Output() toggleRequested = new EventEmitter<void>();

  toggleSection(): void {
    this.section.expanded = !this.section.expanded;
    this.toggleRequested.emit();
  }
}
