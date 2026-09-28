import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';

import { AUDIT_ACTION_LABELS, AuditLogItem } from '../../models/audit.models';
import { AuditLogService } from '../../services/audit-log.service';
import { NotificationService } from '../../services/notification.service';

@Component({
  selector: 'app-audit-log',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './audit-log.component.html',
  styleUrl: './audit-log.component.css',
})
export class AuditLogComponent implements OnInit, OnDestroy {
  items: AuditLogItem[] = [];
  actionType = '';
  entityType = '';
  result = '';
  actor = '';
  occurredFrom = '';
  occurredTo = '';
  page = 1;
  readonly pageSize = 25;
  total = 0;
  loading = false;
  error: string | null = null;
  private readonly destroy$ = new Subject<void>();

  constructor(
    private readonly auditLogService: AuditLogService,
    private readonly notificationService: NotificationService,
  ) {}

  ngOnInit(): void {
    this.load();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  load(): void {
    this.loading = true;
    this.error = null;
    this.auditLogService
      .list(this.page, this.pageSize, this.actionType, this.entityType, this.result, this.actor, this.occurredFrom, this.occurredTo)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.items = response.items;
          this.total = response.total;
          this.loading = false;
        },
        error: (error) => {
          const message = error?.error?.detail || 'Unable to load the audit log.';
          this.error = message;
          this.notificationService.error(message, 'Audit log unavailable');
          this.loading = false;
        },
      });
  }

  applyFilters(): void {
    this.page = 1;
    this.load();
  }

  clearFilters(): void {
    this.actionType = '';
    this.entityType = '';
    this.result = '';
    this.actor = '';
    this.occurredFrom = '';
    this.occurredTo = '';
    this.applyFilters();
  }

  previousPage(): void {
    if (this.page > 1) {
      this.page -= 1;
      this.load();
    }
  }

  nextPage(): void {
    if (this.page * this.pageSize < this.total) {
      this.page += 1;
      this.load();
    }
  }

  get pageCount(): number {
    return Math.max(1, Math.ceil(this.total / this.pageSize));
  }

  actionLabel(actionType: string): string {
    return AUDIT_ACTION_LABELS[actionType] || actionType.replaceAll('_', ' ');
  }
}
