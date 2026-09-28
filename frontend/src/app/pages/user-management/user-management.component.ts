import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';

import { ManagedUser } from '../../models/user.models';
import { NotificationService } from '../../services/notification.service';
import { UserManagementService } from '../../services/user-management.service';

@Component({
  selector: 'app-user-management',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './user-management.component.html',
  styleUrl: './user-management.component.css',
})
export class UserManagementComponent implements OnInit, OnDestroy {
  users: ManagedUser[] = [];
  loading = false;
  showCreate = false;
  editingUser: ManagedUser | null = null;
  resetUser: ManagedUser | null = null;
  editName = '';
  editRole: 'Recruiter' | 'Admin' = 'Recruiter';
  resetPassword = '';
  form = { full_name: '', email: '', password: '', role: 'Recruiter' as 'Recruiter' | 'Admin' };
  private readonly destroy$ = new Subject<void>();

  constructor(
    private readonly usersService: UserManagementService,
    private readonly notifications: NotificationService,
  ) {}

  ngOnInit(): void { this.load(); }
  ngOnDestroy(): void { this.destroy$.next(); this.destroy$.complete(); }

  load(): void {
    this.loading = true;
    this.usersService.list().pipe(takeUntil(this.destroy$)).subscribe({
      next: (users) => { this.users = users; this.loading = false; },
      error: () => { this.loading = false; this.notifications.error('Unable to load users.', 'User management'); },
    });
  }

  create(): void {
    this.usersService.create(this.form).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => { this.showCreate = false; this.form = { full_name: '', email: '', password: '', role: 'Recruiter' }; this.notifications.success('The user was created.', 'User management'); this.load(); },
      error: (error) => this.notifications.error(error?.error?.detail || 'Unable to create user.', 'User management'),
    });
  }

  toggle(user: ManagedUser): void {
    this.usersService.update(user.id, { is_active: !user.is_active }).pipe(takeUntil(this.destroy$)).subscribe({
      next: (updated) => { user.is_active = updated.is_active; this.notifications.success(`User ${updated.is_active ? 'activated' : 'deactivated'}.`, 'User management'); },
      error: () => this.notifications.error('Unable to update user status.', 'User management'),
    });
  }

  beginEdit(user: ManagedUser): void {
    this.editingUser = user;
    this.editName = user.full_name;
    this.editRole = user.role;
  }

  saveEdit(): void {
    if (!this.editingUser) return;
    const editedUser = this.editingUser;
    this.usersService.update(editedUser.id, { full_name: this.editName, role: this.editRole }).pipe(takeUntil(this.destroy$)).subscribe({
      next: (updated) => { Object.assign(editedUser, updated); this.editingUser = null; this.notifications.success('User details updated.', 'User management'); },
      error: (error) => this.notifications.error(error?.error?.detail || 'Unable to update user.', 'User management'),
    });
  }

  beginReset(user: ManagedUser): void { this.resetUser = user; this.resetPassword = ''; }

  saveReset(): void {
    if (!this.resetUser) return;
    this.usersService.resetPassword(this.resetUser.id, this.resetPassword).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => { this.resetUser = null; this.notifications.success('Password reset completed.', 'User management'); },
      error: (error) => this.notifications.error(error?.error?.detail || 'Unable to reset password.', 'User management'),
    });
  }
}
