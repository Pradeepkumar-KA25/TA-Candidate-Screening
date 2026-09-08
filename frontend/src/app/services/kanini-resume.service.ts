import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';

import { ApiConfigService } from '../config/api.config';

export interface KaniniResume {
  id: string;
  filename: string;
  parsed_data: Record<string, any>;
  created_at: string;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: 'builtin' | 'user';
  template_spec?: Record<string, any>;
}

export interface GeneratedResume {
  id: string;
  template_id: string;
  format: 'html' | 'docx' | 'pdf';
  created_at: string;
  download_url: string;
}

@Injectable({
  providedIn: 'root',
})
export class KaniniResumeService {
  private apiBaseUrl: string;

  constructor(
    private readonly httpClient: HttpClient,
    private readonly apiConfig: ApiConfigService
  ) {
    this.apiBaseUrl = this.apiConfig.getApiBaseUrl();
  }

  // ============================================================================
  // RESUME UPLOAD & PARSING
  // ============================================================================

  uploadResume(file: File, llmModel: string = 'auto'): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('llm_model', llmModel);

    return this.httpClient.post(`${this.apiBaseUrl}/kanini/upload`, formData);
  }

  getLlmModels(): Observable<any> {
    return this.httpClient.get(`${this.apiBaseUrl}/kanini/llm-models`);
  }

  // ============================================================================
  // RESUME MANAGEMENT
  // ============================================================================

  listResumes(skip: number = 0, limit: number = 50): Observable<any> {
    const params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    return this.httpClient.get(`${this.apiBaseUrl}/kanini/resumes`, { params });
  }

  getResume(resumeId: string): Observable<KaniniResume> {
    return this.httpClient.get<KaniniResume>(
      `${this.apiBaseUrl}/kanini/resumes/${resumeId}`
    );
  }

  updateResume(resumeId: string, parsedData: Record<string, any>): Observable<any> {
    return this.httpClient.put(
      `${this.apiBaseUrl}/kanini/resumes/${resumeId}`,
      { parsed_data: parsedData }
    );
  }

  deleteResume(resumeId: string): Observable<any> {
    return this.httpClient.delete(
      `${this.apiBaseUrl}/kanini/resumes/${resumeId}`
    );
  }

  // ============================================================================
  // TEMPLATES
  // ============================================================================

  listTemplates(): Observable<{ templates: Template[] }> {
    return this.httpClient.get<{ templates: Template[] }>(
      `${this.apiBaseUrl}/kanini/templates`
    );
  }

  getTemplate(templateId: string): Observable<Template> {
    return this.httpClient.get<Template>(
      `${this.apiBaseUrl}/kanini/templates/${templateId}`
    );
  }

  saveTemplate(
    templateName: string,
    description: string,
    templateSpec: Record<string, any>
  ): Observable<any> {
    const formData = new FormData();
    formData.append('template_name', templateName);
    formData.append('description', description);
    formData.append('template_spec', JSON.stringify(templateSpec));

    return this.httpClient.post(
      `${this.apiBaseUrl}/kanini/templates`,
      formData
    );
  }

  updateTemplate(
    templateId: string,
    templateName: string,
    description: string,
    templateSpec: Record<string, any>
  ): Observable<any> {
    const formData = new FormData();
    formData.append('template_name', templateName);
    formData.append('description', description);
    formData.append('template_spec', JSON.stringify(templateSpec));

    return this.httpClient.put(
      `${this.apiBaseUrl}/kanini/templates/${templateId}`,
      formData
    );
  }

  deleteTemplate(templateId: string): Observable<any> {
    return this.httpClient.delete(
      `${this.apiBaseUrl}/kanini/templates/${templateId}`
    );
  }

  // ============================================================================
  // RENDERING & DOWNLOAD
  // ============================================================================

  renderResume(
    resumeId: string,
    templateId: string,
    format: 'html' | 'docx' | 'pdf' = 'html'
  ): Observable<HttpResponse<Blob>> {
    const formData = new FormData();
    formData.append('resume_id', resumeId);
    formData.append('template_id', templateId);
    formData.append('format', format);

    return this.httpClient.post(
      `${this.apiBaseUrl}/kanini/render`,
      formData,
      { observe: 'response', responseType: 'blob' }
    );
  }

  getPreviewHtml(resumeId: string, templateId: string): Observable<any> {
    return this.httpClient.get(
      `${this.apiBaseUrl}/kanini/preview/${resumeId}/${templateId}`
    );
  }
}
