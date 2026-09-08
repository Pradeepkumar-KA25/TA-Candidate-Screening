import { Component, OnInit, DestroyRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { KaniniResumeService } from '../../services/kanini-resume.service';

interface KaniniResume {
  id: string;
  filename: string;
  parsed_data: any;
  created_at: string;
  updated_at: string;
}

@Component({
  selector: 'app-my-resumes',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './my-resumes.component.html',
  styleUrl: './my-resumes.component.css',
})
export class MyResumesComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);

  resumes: KaniniResume[] = [];
  loading = false;
  error: string | null = null;

  constructor(
    private kaniniResumeService: KaniniResumeService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadResumes();
  }

  loadResumes(): void {
    this.loading = true;
    this.error = null;

    this.kaniniResumeService
      .listResumes(0, 100)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (response: any) => {
          this.resumes = response.resumes || response || [];
          this.loading = false;
        },
        error: (err) => {
          this.error = 'Failed to load resumes. Please try again.';
          this.loading = false;
          console.error('Error loading resumes:', err);
        },
      });
  }

  editResume(resumeId: string): void {
    this.router.navigate(['/resume-generator/review', resumeId]);
  }

  deleteResume(resumeId: string): void {
    if (confirm('Are you sure you want to delete this resume?')) {
      this.loading = true;
      this.kaniniResumeService
        .deleteResume(resumeId)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: () => {
            this.loadResumes();
          },
          error: (err) => {
            this.error = 'Failed to delete resume. Please try again.';
            this.loading = false;
            console.error('Error deleting resume:', err);
          },
        });
    }
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

}
