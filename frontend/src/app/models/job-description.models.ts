export interface JobDescriptionListItem {
  id: string;
  jd_code: string;
  title: string;
  required_skills?: string[];
}

export interface CreateJobDescriptionRequest {
  jd_code: string;
  title: string;
  required_skills: string[];
}

export interface JobDescriptionResponse extends JobDescriptionListItem {
  required_skills: string[];
  created_at: string;
}
