export interface LoginRequest {
  email: string;
  password: string;
  remember_me: boolean;
}

export interface RecruiterProfile {
  id: string;
  full_name: string;
  email: string;
  role: string;
  last_login_at?: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  recruiter: RecruiterProfile;
}

export interface AuthSession {
  token: string;
  tokenType: string;
  expiresIn: number;
  recruiter: RecruiterProfile;
}