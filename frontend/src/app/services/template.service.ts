/**
 * Template Service - API calls for template management
 */

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  TemplateDraft,
  GeneratedTemplateDraft,
  Template,
  TemplateListResponse,
} from '../models/template.model';

@Injectable({
  providedIn: 'root',
})
export class TemplateService {
  private readonly apiUrl = '/api/v1/templates';

  constructor(private http: HttpClient) {}

  /**
   * Step 1: Upload a sample PDF to create a template draft
   */
  uploadSamplePdf(file: File): Observable<TemplateDraft> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<TemplateDraft>(`${this.apiUrl}/drafts`, formData);
  }

  /**
   * Step 2: Generate template specification from draft
   */
  generateTemplateDraft(draftId: string): Observable<GeneratedTemplateDraft> {
    return this.http.post<GeneratedTemplateDraft>(
      `${this.apiUrl}/drafts/${draftId}/generate`,
      {}
    );
  }

  /**
   * Step 3: Save the generated template
   */
  saveTemplateDraft(
    draftId: string,
    name: string,
    description: string
  ): Observable<Template> {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    return this.http.post<Template>(
      `${this.apiUrl}/drafts/${draftId}/save`,
      formData
    );
  }

  /**
   * List all templates for the current user
   */
  listTemplates(skip: number = 0, limit: number = 50): Observable<TemplateListResponse> {
    return this.http.get<TemplateListResponse>(
      `${this.apiUrl}?skip=${skip}&limit=${limit}`
    );
  }

  /**
   * Get a specific template
   */
  getTemplate(templateId: string): Observable<Template> {
    return this.http.get<Template>(`${this.apiUrl}/${templateId}`);
  }

  /**
   * Update template metadata
   */
  updateTemplate(
    templateId: string,
    name?: string,
    description?: string
  ): Observable<Template> {
    const formData = new FormData();
    if (name) formData.append('name', name);
    if (description) formData.append('description', description);
    return this.http.put<Template>(
      `${this.apiUrl}/${templateId}`,
      formData
    );
  }

  /**
   * Delete a template
   */
  deleteTemplate(templateId: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(
      `${this.apiUrl}/${templateId}`
    );
  }
}
