import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { ResumeBuilderService } from './resume-builder.service';
import { ResumeListResponse, ResumeResponse } from '../models/resume.models';
import { ApiConfigService } from '../config/api.config';

describe('ResumeBuilderService', () => {
  let service: ResumeBuilderService;
  let httpMock: HttpTestingController;
  const apiBaseUrl = 'http://localhost:8000/api/v1';

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        ResumeBuilderService,
        {
          provide: ApiConfigService,
          useValue: {
            getApiBaseUrl: () => apiBaseUrl,
          },
        },
      ],
    });

    service = TestBed.inject(ResumeBuilderService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('listResumes', () => {
    it('should fetch list of resumes', (done) => {
      const mockResponse: ResumeListResponse = {
        resumes: [
          {
            id: '123e4567-e89b-12d3-a456-426614174000',
            user_id: '123e4567-e89b-12d3-a456-426614174001',
            session_id: 'session1',
            original_filename: 'resume.pdf',
            file_path: '/path/to/resume.pdf',
            file_size_bytes: 1024,
            file_format: 'pdf',
            parsed_data: { personal_info: { full_name: 'John Doe' } },
            normalization_data: null,
            status: 'completed',
            extra_metadata: null,
            created_at: '2026-01-01T00:00:00Z',
            updated_at: '2026-01-01T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      service.listResumes().subscribe((result) => {
        expect(result.resumes.length).toBe(1);
        expect(result.total_count).toBe(1);
        expect(result.resumes[0].original_filename).toBe('resume.pdf');
        done();
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should handle errors', (done) => {
      const errorMessage = 'Failed to load resumes';

      service.listResumes().subscribe({
        next: () => fail('should have failed with error'),
        error: () => {
          done();
        },
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes`);
      req.error(new ErrorEvent('Network error', { message: errorMessage }));
    });
  });

  describe('getResume', () => {
    it('should fetch a specific resume', (done) => {
      const resumeId = '123e4567-e89b-12d3-a456-426614174000';
      const mockResponse: ResumeResponse = {
        id: resumeId,
        user_id: '123e4567-e89b-12d3-a456-426614174001',
        session_id: 'session1',
        original_filename: 'resume.pdf',
        file_path: '/path/to/resume.pdf',
        file_size_bytes: 1024,
        file_format: 'pdf',
        parsed_data: { personal_info: { full_name: 'John Doe' } },
        normalization_data: null,
        status: 'completed',
        extra_metadata: null,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      };

      service.getResume(resumeId).subscribe((result) => {
        expect(result.id).toBe(resumeId);
        expect(result.original_filename).toBe('resume.pdf');
        done();
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/${resumeId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('deleteResume', () => {
    it('should delete a resume', (done) => {
      const resumeId = '123e4567-e89b-12d3-a456-426614174000';

      service.deleteResume(resumeId).subscribe(() => {
        done();
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/${resumeId}`);
      expect(req.request.method).toBe('DELETE');
      req.flush(null);
    });
  });

  describe('uploadResume', () => {
    it('should upload a resume file', (done) => {
      const file = new File(['content'], 'resume.pdf', { type: 'application/pdf' });
      const mockResponse: ResumeResponse = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        user_id: '123e4567-e89b-12d3-a456-426614174001',
        session_id: 'session1',
        original_filename: 'resume.pdf',
        file_path: '/path/to/resume.pdf',
        file_size_bytes: 7,
        file_format: 'pdf',
        parsed_data: {},
        normalization_data: null,
        status: 'draft',
        extra_metadata: null,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      };

      service.uploadResume(file).subscribe((result) => {
        expect(result.status).toBe('draft');
        expect(result.original_filename).toBe('resume.pdf');
        done();
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/upload`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });
  });

  describe('loading$ and error$', () => {
    it('should emit loading state', (done) => {
      const mockResponse: ResumeListResponse = { resumes: [], total_count: 0 };
      const loadingStates: boolean[] = [];

      service.loading$.subscribe((loading) => {
        loadingStates.push(loading);
      });

      setTimeout(() => {
        service.listResumes().subscribe({
          next: () => {
            setTimeout(() => {
              expect(loadingStates).toContain(true);
              expect(loadingStates[loadingStates.length - 1]).toBe(false);
              done();
            }, 50);
          },
        });

        const req = httpMock.expectOne(`${apiBaseUrl}/resumes`);
        req.flush(mockResponse);
      }, 50);
    });
  });

  describe('updateResume', () => {
    it('should update a resume', (done) => {
      const resumeId = '123e4567-e89b-12d3-a456-426614174000';
      const updateRequest = {
        parsed_data: {
          personal_info: {
            full_name: 'Jane Doe',
            email: 'jane@example.com',
            phone: '555-5678',
          },
          summary: 'Updated summary',
        },
      };

      const mockResponse: ResumeResponse = {
        id: resumeId,
        user_id: '123e4567-e89b-12d3-a456-426614174001',
        session_id: 'session1',
        original_filename: 'resume.pdf',
        file_path: '/path/to/resume.pdf',
        file_size_bytes: 1024,
        file_format: 'pdf',
        parsed_data: updateRequest.parsed_data,
        normalization_data: null,
        status: 'draft',
        extra_metadata: null,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      };

      service.updateResume(resumeId, updateRequest).subscribe((result) => {
        expect(result.id).toBe(resumeId);
        const parsedPersonalInfo = (result.parsed_data['personal_info'] as any);
        expect(parsedPersonalInfo['full_name']).toBe('Jane Doe');
        done();
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/${resumeId}`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual(updateRequest);
      req.flush(mockResponse);
    });

    it('should handle 404 error on update', (done) => {
      const resumeId = '123e4567-e89b-12d3-a456-426614174000';
      const updateRequest = { parsed_data: { personal_info: { full_name: 'Jane' } } };

      service.updateResume(resumeId, updateRequest).subscribe({
        next: () => fail('should have failed with error'),
        error: (error) => {
          expect(error.status).toBe(404);
          done();
        },
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/${resumeId}`);
      req.flush({ detail: 'Resume not found' }, { status: 404, statusText: 'Not Found' });
    });

    it('should handle 401 error on update', (done) => {
      const resumeId = '123e4567-e89b-12d3-a456-426614174000';
      const updateRequest = { parsed_data: { personal_info: { full_name: 'Jane' } } };

      service.updateResume(resumeId, updateRequest).subscribe({
        next: () => fail('should have failed with error'),
        error: (error) => {
          expect(error.status).toBe(401);
          done();
        },
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/${resumeId}`);
      req.flush({ detail: 'Unauthorized' }, { status: 401, statusText: 'Unauthorized' });
    });
  });

  describe('listTemplates', () => {
    it('should fetch list of templates', (done) => {
      const mockResponse = {
        templates: [
          {
            id: 'template-1',
            template_id: 'kanini-default',
            template_name: 'Kanini Template',
            template_type: 'builtin',
            user_id: null,
            is_active: true,
            template_spec: { layout: {} },
            version: '1.0.0',
            extra_metadata: { description: 'Kanini template' },
            created_at: '2026-01-01T00:00:00Z',
            updated_at: '2026-01-01T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      service.listTemplates().subscribe((result) => {
        expect(result.templates.length).toBe(1);
        expect(result.templates[0].template_name).toBe('Kanini Template');
        done();
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/templates`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should handle empty template list', (done) => {
      const mockResponse = { templates: [], total_count: 0 };

      service.listTemplates().subscribe((result) => {
        expect(result.templates.length).toBe(0);
        done();
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/templates`);
      req.flush(mockResponse);
    });

    it('should handle error on listTemplates', (done) => {
      service.listTemplates().subscribe({
        next: () => fail('should have failed with error'),
        error: (error) => {
          expect(error.status).toBe(500);
          done();
        },
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/templates`);
      req.flush({ detail: 'Server error' }, { status: 500, statusText: 'Internal Server Error' });
    });
  });

  describe('getTemplate', () => {
    it('should fetch a single template', (done) => {
      const templateId = 'template-1';
      const mockResponse = {
        id: templateId,
        template_id: 'kanini-default',
        template_name: 'Kanini Template',
        template_type: 'builtin',
        user_id: null,
        is_active: true,
        template_spec: { layout: { columns: 1 } },
        version: '1.0.0',
        extra_metadata: { description: 'Kanini template' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      };

      service.getTemplate(templateId).subscribe((result) => {
        expect(result.id).toBe(templateId);
        expect(result.template_name).toBe('Kanini Template');
        done();
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/templates/${templateId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should handle 404 error on getTemplate', (done) => {
      const templateId = 'template-1';

      service.getTemplate(templateId).subscribe({
        next: () => fail('should have failed with error'),
        error: (error) => {
          expect(error.status).toBe(404);
          done();
        },
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/templates/${templateId}`);
      req.flush({ detail: 'Template not found' }, { status: 404, statusText: 'Not Found' });
    });
  });

  describe('getTemplateQuiet', () => {
    it('should fetch template without changing loading state', (done) => {
      const templateId = 'template-1';
      const mockResponse = {
        id: templateId,
        template_id: 'kanini-default',
        template_name: 'Kanini Template',
        template_type: 'builtin',
        user_id: null,
        is_active: true,
        template_spec: { layout: { columns: 1 } },
        version: '1.0.0',
        extra_metadata: { description: 'Kanini template' },
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      };

      service.getTemplateQuiet(templateId).subscribe((result) => {
        expect(result.id).toBe(templateId);
        expect(result.template_name).toBe('Kanini Template');
        done();
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/templates/${templateId}`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should handle error on getTemplateQuiet', (done) => {
      const templateId = 'template-1';

      service.getTemplateQuiet(templateId).subscribe({
        next: () => fail('should have failed with error'),
        error: (error) => {
          expect(error.status).toBe(500);
          done();
        },
      });

      const req = httpMock.expectOne(`${apiBaseUrl}/resumes/templates/${templateId}`);
      req.flush({ detail: 'Server error' }, { status: 500, statusText: 'Internal Server Error' });
    });
  });
});
