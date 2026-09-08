import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface ShortlistResponse {
  id: string;
  recruiter_id: string;
  jd_id: string;
  candidate_ids: string[];
}

export interface ExportMetadata {
  filename: string;
  candidate_count: number;
  jd_title: string;
  generated_at: string;
}

export interface ShortlistCandidateItem {
  id: string;
  zoho_record_id: string;
  zoho_candidate_id: string | null;
  full_name: string;
  email: string | null;
  phone: string | null;
  total_experience_years: number | null;
  relevant_experience_years: number | null;
  current_company: string | null;
  current_location: string | null;
  preferred_location: string | null;
  notice_period_days: number | null;
  skills: string[] | null;
  degree: string | null;
  normalized_degree: string | null;
  current_ctc: number | null;
  expected_ctc: number | null;
  status: string | null;
  source: string | null;
  created_at: string;
  updated_at: string;
}

export interface ShortlistListItem {
  id: string;
  recruiter_id: string;
  jd_id: string;
  jd_code: string;
  jd_title: string;
  created_at: string;
  candidate_count: number;
  candidates: ShortlistCandidateItem[];
}

@Injectable({
  providedIn: 'root',
})
export class ShortlistService {
  private readonly httpClient = inject(HttpClient);
  private readonly apiBaseUrl = '/api/v1';

  createShortlist(jdId: string, candidateIds: string[]): Observable<ShortlistResponse> {
    return this.httpClient.post<ShortlistResponse>(`${this.apiBaseUrl}/shortlists`, {
      jd_id: jdId,
      candidate_ids: candidateIds,
    });
  }

  listShortlists(jdId?: string): Observable<ShortlistListItem[]> {
    const params: Record<string, string> = {};
    if (jdId) {
      params['jd_id'] = jdId;
    }

    return this.httpClient.get<ShortlistListItem[]>(`${this.apiBaseUrl}/shortlists`, { params });
  }

  removeCandidateFromShortlist(shortlistId: string, candidateId: string): Observable<void> {
    return this.httpClient.delete<void>(`${this.apiBaseUrl}/shortlists/${shortlistId}/candidates/${candidateId}`);
  }

  downloadShortlistAsExcel(shortlistId: string): Observable<ExportMetadata> {
    return this.httpClient.get(`${this.apiBaseUrl}/shortlists/${shortlistId}/export`, {
      responseType: 'blob',
      observe: 'response',
    }).pipe(
      map((response) => {
        // Extract filename from Content-Disposition header
        const contentDisposition = response.headers.get('content-disposition') || '';
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=(["\']?)([^";\n]*)\1/);
        const filename = filenameMatch ? filenameMatch[2] : 'shortlist.xlsx';

        // Trigger browser download
        const blob = response.body || new Blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        window.URL.revokeObjectURL(url);

        // Return metadata for display on success page
        return {
          filename,
          candidate_count: 0, // Will be populated from context
          jd_title: '', // Will be populated from context
          generated_at: new Date().toISOString(),
        };
      })
    );
  }
}

