/**
 * Template Models - TypeScript models for template creation and management
 */

// Template Specification Models
export interface PageSpec {
  size: 'A4' | 'LETTER';
  orientation: 'portrait';
  margin_inches: number;
}

export interface TypographySpec {
  font_family: 'Arial' | 'Calibri' | 'Georgia' | 'Helvetica' | 'Times New Roman';
  base_size_pt: number;
  heading_size_pt: number;
}

export interface ColorSpec {
  text: string;
  accent: string;
  muted: string;
}

export interface HeaderSpec {
  layout: 'centered' | 'left';
  contact_layout: 'inline' | 'stacked';
  show_divider: boolean;
}

export interface LayoutSpec {
  columns: 1 | 2;
  sidebar_position: 'left' | 'right' | 'none';
  section_alignment: 'left' | 'justified';
}

export interface SpacingSpec {
  section_gap_pt: number;
  line_height: number;
  divider_style: 'none' | 'solid' | 'accent';
  skill_style: 'inline' | 'bullets' | 'tags';
}

export interface TemplateSpec {
  page: PageSpec;
  typography: TypographySpec;
  colors: ColorSpec;
  header: HeaderSpec;
  layout: LayoutSpec;
  sections: string[];
  spacing: SpacingSpec;
}

// Template Draft Models
export interface TemplateDraft {
  draft_id: string;
  status: 'uploaded';
  filename: string;
  extracted_data: any;
}

export interface GeneratedTemplateDraft {
  draft_id: string;
  status: 'generated';
  filename: string;
  extracted_data: any;
  template_spec: TemplateSpec;
  preview_html: string;
  suggested_description?: string;
}

// Template Models
export interface Template {
  id: string;
  name: string;
  description: string;
  template_spec: TemplateSpec;
  created_at: string;
}

export interface TemplateListResponse {
  data: Array<{
    id: string;
    name: string;
    description: string;
    created_at: string;
  }>;
  total: number;
}
