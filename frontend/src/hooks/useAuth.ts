'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';

export function useAuth(requiredRole?: 'admin' | 'participant') {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/auth/login');
      return;
    }
    if (requiredRole && user?.role !== requiredRole) {
      router.replace(user?.role === 'admin' ? '/admin' : '/participant');
    }
  }, [isAuthenticated, user, requiredRole, router]);

  return { user, isAuthenticated };
}
