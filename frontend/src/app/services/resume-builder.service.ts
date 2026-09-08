import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, catchError, finalize, of, tap } from 'rxjs';

import {
  GeneratedResumeResponse,
  GenerateResumeRequest,
  ResumeListResponse,
  ResumeResponse,
  ResumeUpdateRequest,
  TemplateListResponse,
  TemplateResponse,
} from '../models/resume.models';
import { ApiConfigService } from '../config/api.config';

@Injectable({
  providedIn: 'root',
})
export class ResumeBuilderService {
  private apiBaseUrl: string;

  private readonly loadingSubject = new BehaviorSubject<boolean>(false);
  private readonly errorSubject = new BehaviorSubject<string | null>(null);

  readonly loading$ = this.loadingSubject.asObservable();
  readonly error$ = this.errorSubject.asObservable();

  constructor(
    private readonly httpClient: HttpClient,
    private readonly apiConfig: ApiConfigService
  ) {
    this.apiBaseUrl = this.apiConfig.getApiBaseUrl();
  }

  /**
   * List all resumes for the current user.
   */
  listResumes(): Observable<ResumeListResponse> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    return this.httpClient.get<ResumeListResponse>(`${this.apiBaseUrl}/resumes`).pipe(
      tap((response) => {
        this.errorSubject.next(null);
      }),
      catchError((error) => {
        const errorMessage = this.extractErrorMessage(error);
        this.errorSubject.next(errorMessage);
        throw error;
      }),
      finalize(() => {
        this.loadingSubject.next(false);
      })
    );
  }

  /**
   * Get a specific resume by ID.
   */
  getResume(resumeId: string): Observable<ResumeResponse> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    return this.httpClient.get<ResumeResponse>(`${this.apiBaseUrl}/resumes/${resumeId}`).pipe(
      tap((response) => {
        this.errorSubject.next(null);
      }),
      catchError((error) => {
        const errorMessage = this.extractErrorMessage(error);
        this.errorSubject.next(errorMessage);
        throw error;
      }),
      finalize(() => {
        this.loadingSubject.next(false);
      })
    );
  }

  /**
   * Upload a new resume file.
   */
  uploadResume(file: File): Observable<ResumeResponse> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    const formData = new FormData();
    formData.append('file', file);

    return this.httpClient.post<ResumeResponse>(`${this.apiBaseUrl}/resumes/upload`, formData).pipe(
      tap((response) => {
        this.errorSubject.next(null);
      }),
      catchError((error) => {
        const errorMessage = this.extractErrorMessage(error);
        this.errorSubject.next(errorMessage);
        throw error;
      }),
      finalize(() => {
        this.loadingSubject.next(false);
      })
    );
  }

  /**
   * Update a resume.
   */
  updateResume(resumeId: string, request: ResumeUpdateRequest): Observable<ResumeResponse> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    return this.httpClient
      .put<ResumeResponse>(`${this.apiBaseUrl}/resumes/${resumeId}`, request)
      .pipe(
        tap((response) => {
          this.errorSubject.next(null);
        }),
        catchError((error) => {
          const errorMessage = this.extractErrorMessage(error);
          this.errorSubject.next(errorMessage);
          throw error;
        }),
        finalize(() => {
          this.loadingSubject.next(false);
        })
      );
  }

  /**
   * Delete a resume.
   */
  deleteResume(resumeId: string): Observable<void> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    return this.httpClient.delete<void>(`${this.apiBaseUrl}/resumes/${resumeId}`).pipe(
      tap(() => {
        this.errorSubject.next(null);
      }),
      catchError((error) => {
        const errorMessage = this.extractErrorMessage(error);
        this.errorSubject.next(errorMessage);
        throw error;
      }),
      finalize(() => {
        this.loadingSubject.next(false);
      })
    );
  }

  /**
   * List all templates accessible to the current user (builtin + user-custom).
   */
  listTemplates(): Observable<TemplateListResponse> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    return this.httpClient.get<TemplateListResponse>(`${this.apiBaseUrl}/resumes/templates`).pipe(
      tap((response) => {
        this.errorSubject.next(null);
      }),
      catchError((error) => {
        const errorMessage = this.extractErrorMessage(error);
        this.errorSubject.next(errorMessage);
        throw error;
      }),
      finalize(() => {
        this.loadingSubject.next(false);
      })
    );
  }

  /**
   * Get a specific template by ID.
   */
  getTemplate(templateId: string): Observable<TemplateResponse> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    return this.httpClient
      .get<TemplateResponse>(`${this.apiBaseUrl}/resumes/templates/${templateId}`)
      .pipe(
        tap((response) => {
          this.errorSubject.next(null);
        }),
        catchError((error) => {
          const errorMessage = this.extractErrorMessage(error);
          this.errorSubject.next(errorMessage);
          throw error;
        }),
        finalize(() => {
          this.loadingSubject.next(false);
        })
      );
  }

  /**
   * Generate a DOCX resume using a template.
   */
  generateDocx(resumeId: string, templateId: string): Observable<GeneratedResumeResponse> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    const request: GenerateResumeRequest = { template_id: templateId };

    return this.httpClient
      .post<GeneratedResumeResponse>(`${this.apiBaseUrl}/resumes/${resumeId}/render`, request)
      .pipe(
        tap((response) => {
          this.errorSubject.next(null);
        }),
        catchError((error) => {
          const errorMessage = this.extractErrorMessage(error);
          this.errorSubject.next(errorMessage);
          throw error;
        }),
        finalize(() => {
          this.loadingSubject.next(false);
        })
      );
  }

  /**
   * Download a generated DOCX file.
   * Returns a Blob that can be used with FileSaver or download links.
   */
  downloadDocx(resumeId: string, generatedId: string): Observable<Blob> {
    return this.httpClient.get(
      `${this.apiBaseUrl}/resumes/${resumeId}/outputs/${generatedId}`,
      {
        responseType: 'blob',
      }
    );
  }

  /**
   * Delete a generated resume file.
   */
  deleteGenerated(resumeId: string, generatedId: string): Observable<void> {
    this.loadingSubject.next(true);
    this.errorSubject.next(null);

    return this.httpClient
      .delete<void>(`${this.apiBaseUrl}/resumes/${resumeId}/outputs/${generatedId}`)
      .pipe(
        tap(() => {
          this.errorSubject.next(null);
        }),
        catchError((error) => {
          const errorMessage = this.extractErrorMessage(error);
          this.errorSubject.next(errorMessage);
          throw error;
        }),
        finalize(() => {
          this.loadingSubject.next(false);
        })
      );
  }

  /**
   * Get a specific template by ID without changing loading state.
   * Used when template details are needed quietly (not affecting global loading state).
   */
  getTemplateQuiet(templateId: string): Observable<TemplateResponse> {
    return this.httpClient
      .get<TemplateResponse>(`${this.apiBaseUrl}/resumes/templates/${templateId}`)
      .pipe(
        catchError((error) => {
          const errorMessage = this.extractErrorMessage(error);
          this.errorSubject.next(errorMessage);
          throw error;
        })
      );
  }

  /**
   * Extract user-friendly error message from HTTP error.
   */
  private extractErrorMessage(error: unknown): string {
    if (error instanceof Error) {
      if ('error' in error && typeof error.error === 'object' && error.error !== null) {
        const errorObj = error.error as Record<string, unknown>;
        if ('detail' in errorObj && typeof errorObj['detail'] === 'string') {
          return errorObj['detail'] as string;
        }
      }
      return error.message || 'An error occurred';
    }
    return 'An unexpected error occurred';
  }
}
