import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-status-pill',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './status-pill.component.html',
  styleUrl: './status-pill.component.css',
})
export class StatusPillComponent {
  @Input() labelPrefix = 'Zoho Recruit';
  @Input() state: 'connected' | 'disconnected' = 'disconnected';

  get stateLabel(): string {
    return this.state === 'connected' ? 'Connected' : 'Disconnected';
  }
}
