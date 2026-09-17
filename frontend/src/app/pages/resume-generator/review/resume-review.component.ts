import { Component, OnInit, signal, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormArray, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { KaniniResumeService } from '../../../services/kanini-resume.service';
import { ResumeData } from '../../../models/resume.model';
import { Subject, takeUntil, timeout } from 'rxjs';

@Component({
  selector: 'app-resume-review',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  styleUrls: ['./resume-review.component.scss'],
  template: `
    <section class="review" [attr.aria-labelledby]="'review-title'" *ngIf="!loading() && !error()">
      <header>
        <div>
          <p class="eyebrow">Step 2 of 5</p>
          <h1 id="review-title">Review resume details</h1>
          <p class="muted">{{ form.dirty ? 'Unsaved changes' : 'All changes saved' }}</p>
        </div>
        <button type="button" class="ui-button" (click)="cancel()">Cancel</button>
      </header>

      <form [formGroup]="form" (ngSubmit)="save()">

        <!-- Contact Information - Only Name visible -->
        <section formGroupName="contact">
          <h2>Candidate Name</h2>
          <div class="form-grid">
            <label>
              Name *
              <input formControlName="name" />
            </label>
            <!-- Hidden fields kept for form data binding -->
            <input type="hidden" formControlName="email" />
            <input type="hidden" formControlName="phone" />
            <input type="hidden" formControlName="location" />
            <input type="hidden" formControlName="linkedin" />
            <input type="hidden" formControlName="github" />
          </div>
        </section>

        <!-- Professional Summary -->
        <section>
          <label>
            Professional summary
            <textarea formControlName="summary"></textarea>
          </label>
        </section>

        <!-- Skills -->
        <section>
          <label>
            Skills by category
            <textarea
              formControlName="skills"
              placeholder="Python: Django, Flask&#10;JavaScript: React, Angular&#10;Databases: PostgreSQL, MongoDB"
            ></textarea>
          </label>
        </section>

        <!-- Experience -->
        <section>
          <div class="section-head">
            <h2>Experience</h2>
            <button
              type="button"
              class="ui-button ui-button--secondary ui-button--compact"
              (click)="addExperience()"
            >
              Add experience
            </button>
          </div>
          <div formArrayName="experience">
            <fieldset
              class="repeat"
              *ngFor="let item of experience.controls; let i = index"
              [formGroupName]="i"
            >
              <legend>Experience {{ i + 1 }}</legend>
              <label>
                Company
                <input formControlName="company" placeholder="e.g. Acme Corp" />
              </label>
              <label>
                Designation
                <input formControlName="title" placeholder="e.g. Senior Engineer" />
              </label>
              <label>
                Duration
                <input formControlName="dates" placeholder="e.g. Jan 2022 - Present" />
              </label>
              <label>
                Responsibilities
                <textarea formControlName="responsibilities" placeholder="One per line"></textarea>
              </label>
              <button
                type="button"
                class="repeat-action"
                (click)="removeExperience(i)"
              >
                Remove experience
              </button>
            </fieldset>
          </div>
        </section>

        <!-- Projects -->
        <section>
          <div class="section-head">
            <h2>Projects</h2>
            <button
              type="button"
              class="ui-button ui-button--secondary ui-button--compact"
              (click)="addProject()"
            >
              Add project
            </button>
          </div>
          <div formArrayName="projects">
            <fieldset
              class="repeat"
              *ngFor="let item of projects.controls; let i = index"
              [formGroupName]="i"
            >
              <legend>Project {{ i + 1 }}</legend>
              <label>
                Project Name
                <input formControlName="name" placeholder="e.g. E-Commerce Platform" />
              </label>
              <label>
                Client
                <input formControlName="client" placeholder="e.g. Contoso Inc" />
              </label>
              <label>
                Role
                <input formControlName="role" placeholder="e.g. Lead Developer" />
              </label>
              <label>
                Duration
                <input formControlName="duration" placeholder="e.g. 6 months" />
              </label>
              <label>
                Technologies
                <input formControlName="technologies" placeholder="e.g. Python, React, PostgreSQL" />
              </label>
              <label>
                Description
                <textarea formControlName="description" placeholder="Brief summary"></textarea>
              </label>
              <label>
                Responsibilities
                <textarea formControlName="responsibilities" placeholder="One per line"></textarea>
              </label>
              <button
                type="button"
                class="repeat-action"
                (click)="removeProject(i)"
              >
                Remove project
              </button>
            </fieldset>
          </div>
        </section>

        <!-- Education & Certifications -->
        <section>
          <div class="form-grid">
            <label>
              Education
              <textarea
                formControlName="education"
                placeholder="B.S. Computer Science | 2020 | MIT | 3.8"
              ></textarea>
            </label>
            <label>
              Certifications
              <textarea
                formControlName="certifications"
                placeholder="One per line"
              ></textarea>
            </label>
            <label>
              Achievements
              <textarea
                formControlName="achievements"
                placeholder="One per line"
              ></textarea>
            </label>
          </div>
        </section>

        <footer>
          <button type="button" class="ui-button" (click)="cancel()">Back</button>
          <button
            type="submit"
            class="ui-button primary"
            [disabled]="saving() || !form.valid"
          >
            {{ saving() ? 'Saving...' : 'Save & Continue' }}
          </button>
        </footer>
      </form>
    </section>

    <div *ngIf="loading()" style="padding: 40px; text-align: center;">
      <p>Loading resume details...</p>
    </div>

    <div *ngIf="!loading() && error()" style="padding: 40px; text-align: center;" role="alert">
      <p class="error">{{ error() }}</p>
      <button type="button" class="ui-button secondary" (click)="loadResume()" style="margin-top: 20px;">
        Try again
      </button>
    </div>
  `,
})
export class ResumeReviewComponent implements OnInit, OnDestroy {
  private fb = inject(FormBuilder);
  private kaniniService = inject(KaniniResumeService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private destroy$ = new Subject<void>();

  resumeId = '';
  loading = signal(true);
  saving = signal(false);
  error = signal('');

  form = this.fb.nonNullable.group({
    contact: this.fb.nonNullable.group({
      name: ['', Validators.required],
      email: ['', [Validators.email]],
      phone: [''],
      location: [''],
      linkedin: [''],
      github: [''],
    }),
    summary: [''],
    skills: [''],
    experience: this.fb.array([]),
    projects: this.fb.array([]),
    education: [''],
    certifications: [''],
    achievements: [''],
  });

  get experience(): FormArray {
    return this.form.get('experience') as FormArray;
  }

  get projects(): FormArray {
    return this.form.get('projects') as FormArray;
  }

  ngOnInit(): void {
    // Subscribe to route params changes to handle navigation
    this.route.params.pipe(takeUntil(this.destroy$)).subscribe((params) => {
      this.resumeId = params['resumeId'] || '';
      if (this.resumeId) {
        this.loadResume();
      } else {
        this.error.set('Invalid resume ID');
        this.loading.set(false);
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadResume(): void {
    if (!this.resumeId) {
      this.error.set('No resume ID provided');
      this.loading.set(false);
      return;
    }

    this.loading.set(true);
    this.error.set('');

    this.kaniniService
      .getResume(this.resumeId)
      .pipe(
        timeout(30000), // 30 second timeout
        takeUntil(this.destroy$)
      )
      .subscribe({
        next: (resume) => {
          try {
            this.populateForm(resume['parsed_data']);
            this.loading.set(false);
          } catch (e) {
            this.error.set('Failed to parse resume data');
            this.loading.set(false);
          }
        },
        error: (err) => {
          console.error('Resume load error:', err);
          let errorMsg = 'Failed to load resume';
          if (err?.status === 401) {
            errorMsg = 'Session expired. Please login again';
          } else if (err?.status === 404) {
            errorMsg = 'Resume not found';
          } else if (err?.status === 403) {
            errorMsg = 'Access denied';
          } else if (err?.name === 'TimeoutError') {
            errorMsg = 'Request timed out. Please try again';
          }
          this.error.set(errorMsg);
          this.loading.set(false);
        },
      });
  }

  private populateForm(data: any): void {
    console.log('=== Resume Data Received ===');
    console.log('Full parsed_data:', data);
    console.log('Experience count:', data.experience?.length || 0);
    
    // Set contact info
    this.form.patchValue({
      contact: data.contact,
      summary: data.summary,
      skills: this.formatSkills(data.skills),
      education: this.formatEducation(data.education),
      certifications: data.certifications.join('\n'),
      achievements: data.achievements.join('\n'),
    });

    // Add experience items
    data.experience.forEach((exp: any, idx: number) => {
      console.log(`Experience ${idx + 1}:`, exp);
      
      // Extract title with multiple fallback options
      let titleValue = exp.title || exp.designation || exp.jobTitle || exp.role || '';
      
      // If title is still empty, log warning for debugging
      if (!titleValue) {
        console.warn(`Experience ${idx + 1} missing title:`, exp);
      } else {
        console.log(`Experience ${idx + 1} title: "${titleValue}"`);
      }
      
      this.experience.push(
        this.fb.nonNullable.group({
          company: exp.company || exp.company_name || '',
          title: titleValue,
          dates: exp.dates || exp.duration || '',
          responsibilities: Array.isArray(exp.responsibilities) 
            ? exp.responsibilities.join('\n') 
            : (exp.responsibilities || ''),
        })
      );
    });

    // Add project items
    data.projects.forEach((proj: any) => {
      this.projects.push(
        this.fb.nonNullable.group({
          name: proj.name || '',
          client: proj.client || '',
          role: proj.role || '',
          duration: proj.duration || '',
          technologies: (proj.technologies || []).join(', '),
          description: proj.description || '',
          responsibilities: (proj.responsibilities || []).join('\n'),
        })
      );
    });

    this.form.markAsPristine();
  }

  private formatSkills(skills: Record<string, string[]>): string {
    return Object.entries(skills || {})
      .map(([category, items]) => `${category}: ${items.join(', ')}`)
      .join('\n');
  }

  private formatEducation(education: Array<any>): string {
    return (education || [])
      .map((edu) => [edu.degree, edu.year, edu.institution, edu.gpa].filter(Boolean).join(' | '))
      .join('\n');
  }

  private parseSkills(text: string): Record<string, string[]> {
    const result: Record<string, string[]> = {};
    (text || '').split('\n').forEach((line) => {
      const [category, ...items] = line.split(':');
      if (category.trim()) {
        result[category.trim()] = items
          .join(':')
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean);
      }
    });
    return result;
  }

  private parseEducation(text: string): Array<any> {
    return (text || '')
      .split('\n')
      .filter(Boolean)
      .map((line) => {
        const [degree = '', year = '', institution = '', gpa = ''] = line.split('|').map((x) => x.trim());
        return { degree, year, institution, gpa };
      });
  }

  private parseList(text: string): string[] {
    return (text || '').split('\n').map((x) => x.trim()).filter(Boolean);
  }

  addExperience(): void {
    this.experience.push(
      this.fb.nonNullable.group({
        company: '',
        title: '',
        dates: '',
        responsibilities: '',
      })
    );
  }

  removeExperience(index: number): void {
    this.experience.removeAt(index);
  }

  addProject(): void {
    this.projects.push(
      this.fb.nonNullable.group({
        name: '',
        client: '',
        role: '',
        duration: '',
        technologies: '',
        description: '',
        responsibilities: '',
      })
    );
  }

  removeProject(index: number): void {
    this.projects.removeAt(index);
  }

  cancel(): void {
    if (this.form.dirty && !confirm('Discard unsaved changes?')) {
      return;
    }
    this.router.navigate(['/resume-generator']);
  }

  save(): void {
    if (!this.form.valid) {
      this.error.set('Please fix the errors in the form');
      return;
    }

    this.saving.set(true);
    const raw = this.form.getRawValue();

    const payload: any = {
      contact: raw.contact,
      summary: raw.summary,
      skills: this.parseSkills(raw.skills),
      experience: (raw.experience || []).map((exp: any) => ({
        ...exp,
        company_name: exp.company,
        company_sector: '',
        location: '',
        responsibilities: this.parseList(exp.responsibilities),
        projects: [],
      })),
      projects: (raw.projects || []).map((proj: any) => ({
        ...proj,
        technologies: this.parseList(proj.technologies),
        responsibilities: this.parseList(proj.responsibilities),
      })),
      education: this.parseEducation(raw.education),
      certifications: this.parseList(raw.certifications),
      achievements: this.parseList(raw.achievements),
      additional_sections: {},
    };

    this.kaniniService.updateResume(this.resumeId, payload).subscribe({
      next: () => {
        this.saving.set(false);
        this.form.markAsPristine();
        this.router.navigate(['/resume-generator/templates', this.resumeId]);
      },
      error: (err) => {
        this.saving.set(false);
        this.error.set(err?.error?.detail || 'Failed to save resume');
      },
    });
  }
}
