import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FieldItem } from '../../services/candidate-fields.service';

@Component({
  selector: 'app-candidate-field-item',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="field-item" [class.empty-field]="field.isEmpty">
      <dt class="field-label">{{ field.displayName }}</dt>
      <dd class="field-value" [class.empty-value]="field.isEmpty">
        <span class="field-content">{{ field.formatted }}</span>
        <span class="field-type" *ngIf="showFieldType" title="Field type">{{ field.type }}</span>
      </dd>
    </div>
  `,
  styles: [`
    .field-item {
      display: grid;
      grid-template-columns: 250px 1fr;
      gap: 16px;
      padding: 12px 0;
      border-bottom: 1px solid var(--border-color);
      align-items: start;
      transition: color 0.2s ease, border-color 0.2s ease;
    }

    .field-item:last-child {
      border-bottom: none;
    }

    .field-item.empty-field .field-label {
      color: var(--text-muted);
      font-style: italic;
    }

    .field-label {
      font-weight: 600;
      color: var(--text-primary);
      word-break: break-word;
      transition: color 0.2s ease;
    }

    .field-value {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
    }

    .field-value.empty-value {
      color: var(--text-muted);
      font-style: italic;
    }

    .field-content {
      flex: 1;
      word-break: break-word;
      white-space: pre-wrap;
      line-height: 1.4;
    }

    .field-type {
      display: inline-block;
      padding: 2px 6px;
      background-color: var(--surface-strong);
      color: var(--text-muted);
      font-size: 0.75rem;
      border-radius: 3px;
      opacity: 0.6;
      transition: background-color 0.2s ease, color 0.2s ease;
    }

    @media (max-width: 768px) {
      .field-item {
        grid-template-columns: 1fr;
        gap: 4px;
      }

      .field-label {
        font-size: 0.875rem;
      }
    }
  `]
})
export class CandidateFieldItemComponent {
  @Input() field!: FieldItem;
  @Input() showFieldType = false;
}
