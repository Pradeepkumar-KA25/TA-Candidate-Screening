export interface ManagedUser {
  id: string;
  full_name: string;
  email: string;
  role: 'Recruiter' | 'Admin';
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface CreateUserRequest {
  full_name: string;
  email: string;
  password: string;
  role: 'Recruiter' | 'Admin';
}
