import { useAuthStore } from '@/store/auth';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function requireAuth() {
  if (!isAuthenticated() && typeof window !== 'undefined') {
    window.location.href = '/auth/login';
  }
}
