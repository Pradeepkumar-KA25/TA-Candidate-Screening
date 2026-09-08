// Resume data models matching Kanini structure

export interface ContactInfo {
  name: string;
  email: string;
  phone: string;
  location: string;
  linkedin: string;
  github: string;
}

export interface Experience {
  company: string;
  company_name: string;
  company_sector: string;
  title: string;
  location: string;
  dates: string;
  responsibilities: string[];
  projects: Project[];
}

export interface Education {
  degree: string;
  institution: string;
  year: string;
  gpa: string;
}

export interface Project {
  name: string;
  client: string;
  duration: string;
  role: string;
  description: string;
  technologies: string[];
  responsibilities: string[];
}

export interface ResumeData {
  contact: ContactInfo;
  summary: string;
  skills: Record<string, string[]>;
  experience: Experience[];
  education: Education[];
  certifications: string[];
  achievements: string[];
  projects: Project[];
  additional_sections: Record<string, any>;
}

export interface TemplateMetadata {
  id: string;
  name: string;
  display_name?: string;
  description: string;
  enabled?: boolean;
  supported_outputs?: Array<'html' | 'docx' | 'pdf'>;
  page_size?: 'LETTER' | 'A4';
  category: 'builtin' | 'user';
  user_created?: boolean;
}

export interface UploadResponse {
  resume_id: string;
  filename: string;
  parsed_data: ResumeData;
}

export interface PreviewResponse {
  html: string;
}

export interface RenderResponse {
  generated_id: string;
  resume_id: string;
  template_id: string;
  format: string;
}

export interface SavedResumeSummary {
  id: string;
  filename: string;
  created_at: string;
}
