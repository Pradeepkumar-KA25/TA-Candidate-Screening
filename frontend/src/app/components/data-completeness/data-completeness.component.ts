import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-data-completeness',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="completeness-container">
      <div class="completeness-header">
        <span class="completeness-label">Data Completeness</span>
        <span class="completeness-percentage" [ngClass]="getColorClass()">
          {{ percentage }}%
        </span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" [style.width.%]="percentage"></div>
      </div>
      <div class="completeness-info">
        <span class="info-text">{{ getCompletionMessage() }}</span>
      </div>
    </div>
  `,
  styles: [`
    .completeness-container {
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 20px;
    }

    .completeness-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }

    .completeness-label {
      font-weight: 600;
      color: #374151;
      font-size: 0.95rem;
    }

    .completeness-percentage {
      font-weight: 700;
      font-size: 1.25rem;
    }

    .progress-bar {
      width: 100%;
      height: 12px;
      background: #e5e7eb;
      border-radius: 6px;
      overflow: hidden;
      margin-bottom: 12px;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #ef4444 0%, #f97316 30%, #eab308 60%, #22c55e 100%);
      transition: width 0.5s ease-out;
    }

    .completeness-info {
      text-align: center;
    }

    .info-text {
      font-size: 0.875rem;
      color: #6b7280;
    }
  `]
})
export class DataCompletenessComponent {
  @Input() percentage: number = 0;

  getColorClass(): string {
    if (this.percentage >= 70) return 'text-green-600';
    if (this.percentage >= 40) return 'text-orange-600';
    return 'text-red-600';
  }

  getCompletionMessage(): string {
    if (this.percentage >= 90) {
      return '🎉 Excellent! Profile is nearly complete';
    }
    if (this.percentage >= 70) {
      return '✓ Good! Most important information is present';
    }
    if (this.percentage >= 40) {
      return '⚠ Fair - Some key information is missing';
    }
    return '⚠ Poor - Important fields need to be filled';
  }
}
