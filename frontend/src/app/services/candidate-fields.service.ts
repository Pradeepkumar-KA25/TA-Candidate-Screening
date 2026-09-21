import { Injectable } from '@angular/core';

export interface FieldGroup {
  category: string;
  description: string;
  expanded: boolean;
  fields: FieldItem[];
}

export interface FieldItem {
  key: string;
  displayName: string;
  value: any;
  type: string;
  isEmpty: boolean;
  formatted: string;
}

@Injectable({
  providedIn: 'root'
})
export class CandidateFieldsService {

  /**
   * Group candidate fields from pre-organized extended_fields structure.
   * The backend already organizes fields into categories, so we just need to
   * convert them to our FieldGroup format for display.
   */
  groupCandidateFields(extendedFields: any): FieldGroup[] {
    const groups: FieldGroup[] = [];

    if (!extendedFields) {
      return groups;
    }

    // Map of backend category names to display names and expansion state
    const categoryConfig = {
      'personal_contact': { displayName: 'Personal Information', expanded: true },
      'contact_address': { displayName: 'Contact & Address', expanded: true },
      'professional_details': { displayName: 'Professional Details', expanded: true },
      'education_qualifications': { displayName: 'Education & Qualifications', expanded: true },
      'application_recruitment': { displayName: 'Application & Recruitment', expanded: true },
      'employment': { displayName: 'Employment Details', expanded: false },
      'interview_process': { displayName: 'Interview Process', expanded: false },
      'candidate_lifecycle': { displayName: 'Candidate Lifecycle', expanded: false },
      'salary_benefits': { displayName: 'Salary & Benefits', expanded: false },
      'referral_vendor_sourcing': { displayName: 'Referral & Sourcing', expanded: false },
      'system_metadata': { displayName: 'System & Metadata', expanded: false },
      'other_fields': { displayName: 'Other Fields', expanded: false }
    };

    // Process each category
    Object.entries(categoryConfig).forEach(([key, config]) => {
      const categoryData = (extendedFields as any)[key];

      if (categoryData && typeof categoryData === 'object' && Object.keys(categoryData).length > 0) {
        const fields: FieldItem[] = [];

        // Convert each field in the category to FieldItem
        Object.entries(categoryData).forEach(([fieldName, fieldValue]) => {
          fields.push(this.createFieldItem(fieldName, fieldValue));
        });

        if (fields.length > 0) {
          groups.push({
            category: config.displayName,
            description: config.displayName,
            expanded: config.expanded,
            fields: fields
          });
        }
      }
    });

    return groups;
  }

  /**
   * Calculate data completeness percentage
   */
  calculateCompleteness(extendedFields: any): number {
    if (!extendedFields) {
      return 0;
    }

    let total = 0;
    let populated = 0;

    // Count fields across all categories in extended_fields
    Object.entries(extendedFields).forEach(([categoryKey, categoryData]: [string, any]) => {
      // Skip metadata and empty fields sections for completeness calculation
      if (categoryKey === 'system_metadata' || categoryKey === 'other_fields') {
        return;
      }

      if (categoryData && typeof categoryData === 'object') {
        Object.values(categoryData).forEach((value: any) => {
          total++;
          // Count as populated only if not empty marker and not null/undefined
          const strValue = String(value).trim();
          if (strValue && strValue !== '—' && strValue !== 'null' && strValue !== 'undefined') {
            populated++;
          }
        });
      }
    });

    if (total === 0) {
      return 0;
    }

    return Math.round((populated / total) * 100);
  }

  /**
   * Get display name for a field key
   */
  getDisplayName(key: string): string {
    // Convert snake_case to Title Case
    return key
      .replace(/_/g, ' ')
      .replace(/\$/, '')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  }

  /**
   * Format field value based on type
   */
  formatFieldValue(value: any): string {
    if (value === null || value === undefined) {
      return '—';
    }

    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }

    if (typeof value === 'object') {
      if (Array.isArray(value)) {
        // For arrays, join non-empty values
        const filtered = value.filter((v: any) => v !== null && v !== undefined && String(v).trim());
        return filtered.length > 0 ? filtered.join(', ') : '—';
      }
      // For objects, try to extract meaningful value
      const entries = Object.entries(value);
      if (entries.length === 0) {
        return '{}';
      }
      // Get the first value or create a summary
      const firstValue = entries[0][1];
      if (typeof firstValue === 'object' && firstValue !== null && !Array.isArray(firstValue)) {
        // Nested object - create a summary
        return `{${entries.length} properties}`;
      }
      // Return the first value
      return String(firstValue).trim() || '—';
    }

    const strValue = String(value).trim();
    return strValue || '—';
  }

  /**
   * Get color class for completeness percentage
   */
  getCompletenessColor(percentage: number): string {
    if (percentage >= 70) return 'text-green-600';
    if (percentage >= 40) return 'text-orange-600';
    return 'text-red-600';
  }

  /**
   * Private helper methods
   */
  private normalizePayload(payload: any): Record<string, any> {
    if (typeof payload === 'string') {
      try {
        return JSON.parse(payload);
      } catch {
        return {};
      }
    }
    return payload || {};
  }

  private createFieldItem(key: string, value: any): FieldItem {
    return {
      key: key,
      displayName: this.getDisplayName(key),
      value: value,
      type: this.getFieldType(value),
      isEmpty: value === null || value === undefined || !String(value).trim(),
      formatted: this.formatFieldValue(value)
    };
  }

  private getFieldType(value: any): string {
    if (value === null || value === undefined) return 'empty';
    if (typeof value === 'boolean') return 'boolean';
    if (typeof value === 'number') return 'number';
    if (Array.isArray(value)) return 'array';
    if (typeof value === 'object') return 'object';
    return 'string';
  }
}
