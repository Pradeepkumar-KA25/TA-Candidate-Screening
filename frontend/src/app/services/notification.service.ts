import { Injectable, inject } from '@angular/core';
import { ToastrService } from 'ngx-toastr';

@Injectable({ providedIn: 'root' })
export class NotificationService {
  private readonly toastr = inject(ToastrService, { optional: true });

  success(message: string, title = 'Success'): void {
    this.toastr?.success(message, title);
  }

  info(message: string, title = 'Information'): void {
    this.toastr?.info(message, title);
  }

  warning(message: string, title = 'Attention'): void {
    this.toastr?.warning(message, title);
  }

  error(message: string, title = 'Something went wrong'): void {
    this.toastr?.error(message, title);
  }
}
