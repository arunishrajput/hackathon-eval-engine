'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar } from '@/components/layout/Sidebar';
import { Navbar } from '@/components/layout/Navbar';
import { useAuthStore } from '@/store/auth';

export default function ParticipantLayout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/auth/login');
      return;
    }
    if (user && user.role === 'admin') {
      router.replace('/admin');
    }
  }, [isAuthenticated, user, router]);

  // Render nothing while redirecting
  if (!isAuthenticated || (user && user.role === 'admin')) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#13141a]">
        <span className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#13141a] overflow-hidden">
      <Sidebar role="participant" />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <Navbar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
