/**
 * Resume response from backend API.
 * Represents a single resume with parsed data and metadata.
 */
export interface ResumeResponse {
  id: string; // UUID
  user_id: string; // UUID
  session_id: string;
  original_filename: string;
  file_path: string;
  file_size_bytes: number | null;
  file_format: string; // "pdf", "docx", "doc"
  parsed_data: Record<string, unknown>;
  normalization_data: Record<string, unknown> | null;
  status: string; // "draft", "completed"
  extra_metadata: Record<string, unknown> | null;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

/**
 * List response from backend API.
 * Contains array of resumes and total count.
 */
export interface ResumeListResponse {
  resumes: ResumeResponse[];
  total_count: number;
}

/**
 * Request to update a resume.
 */
export interface ResumeUpdateRequest {
  parsed_data?: Record<string, unknown>;
  normalization_data?: Record<string, unknown>;
  extra_metadata?: Record<string, unknown>;
  status?: string;
}

/**
 * Template response from backend API.
 * Represents a template (builtin or user-custom).
 */
export interface TemplateResponse {
  id: string; // UUID
  template_id: string;
  template_name: string;
  template_type: string;
  user_id: string | null; // null for builtin templates
  is_active: boolean;
  template_spec: Record<string, unknown>;
  version: string | null;
  extra_metadata: Record<string, unknown> | null;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

/**
 * List response for templates.
 */
export interface TemplateListResponse {
  templates: TemplateResponse[];
  total_count: number;
}

/**
 * Generated resume (DOCX output) response from backend API.
 */
export interface GeneratedResumeResponse {
  id: string; // UUID
  resume_id: string; // UUID
  template_id: string; // UUID
  format: string; // "docx"
  file_path: string;
  file_size_bytes: number | null;
  generation_status: string; // "generated", "generating", "failed"
  generation_error: string | null;
  extra_metadata: Record<string, unknown> | null;
  generated_at: string; // ISO datetime
}

/**
 * Request to generate a resume.
 */
export interface GenerateResumeRequest {
  template_id: string; // UUID
}

/**
 * Parsed resume data structure.
 * Represents the extracted and structured resume information.
 */
export interface ParsedResumeData {
  personal_info?: {
    full_name?: string;
    email?: string;
    phone?: string;
    location?: string;
    linkedin?: string;
    portfolio?: string;
  };
  summary?: string;
  skills?: string[];
  experience?: Array<{
    company?: string;
    position?: string;
    start_date?: string;
    end_date?: string;
    description?: string;
  }>;
  education?: Array<{
    institution?: string;
    degree?: string;
    field?: string;
    graduation_year?: string;
  }>;
  certifications?: Array<{
    name?: string;
    issuer?: string;
    date?: string;
  }>;
  projects?: Array<{
    name?: string;
    description?: string;
    date?: string;
  }>;
  [key: string]: unknown; // Allow for additional fields
}

/**
 * Resume status type.
 */
export type ResumeStatus = 'draft' | 'completed';

/**
 * Generation status type.
 */
export type GenerationStatus = 'generating' | 'generated' | 'failed';
