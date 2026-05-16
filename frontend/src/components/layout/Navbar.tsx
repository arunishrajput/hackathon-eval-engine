'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';

const adminLinks = [
  { href: '/admin', label: 'Dashboard' },
  { href: '/admin/hackathons/new', label: 'New Hackathon' },
];

const participantLinks = [
  { href: '/participant', label: 'Home' },
  { href: '/participant/hackathons', label: 'Hackathons' },
];

export function Navbar() {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    logout();
    router.replace('/auth/login');
  };

  const isAdmin = user?.role === 'admin';
  const navLinks = isAdmin ? adminLinks : participantLinks;

  const initials = user
    ? (user.full_name ?? user.email).charAt(0).toUpperCase()
    : '?';

  return (
    <header
      className="border-b flex items-center justify-between flex-shrink-0 gap-4 px-5 py-2.5"
      style={{ background: '#13141a', borderColor: '#2d2e3a' }}
    >
      {/* Logo + nav */}
      <div className="flex items-center gap-5 min-w-0">
        <Link
          href={isAdmin ? '/admin' : '/participant'}
          className="flex items-center gap-2 flex-shrink-0"
        >
          {/* Red square logo mark */}
          <div
            className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0"
            style={{ background: '#b1361e' }}
          >
            <svg
              className="w-3.5 h-3.5 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <span className="text-sm font-bold tracking-tight" style={{ color: '#dddfe4' }}>
            EVAL<span style={{ color: '#b1361e' }}>ON</span>
          </span>
        </Link>

        {/* Role-aware nav links */}
        <nav className="hidden sm:flex items-center">
          {navLinks.map((link) => {
            const active =
              link.href === '/admin' || link.href === '/participant'
                ? pathname === link.href
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className="relative px-3 py-2 text-sm font-medium transition-colors"
                style={{ color: active ? '#dddfe4' : '#7e8088' }}
              >
                {link.label}
                {active && (
                  <span
                    className="absolute bottom-0 left-3 right-3 h-[2px] rounded-t-sm"
                    style={{ background: '#b1361e' }}
                  />
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2.5 flex-shrink-0">
        {/* Role badge */}
        {user && (
          <span
            className="hidden md:inline-block text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border"
            style={
              isAdmin
                ? {
                    color: '#c084fc',
                    borderColor: 'rgba(168,85,247,0.3)',
                    background: 'rgba(88,28,135,0.2)',
                  }
                : {
                    color: '#7e8088',
                    borderColor: '#2d2e3a',
                    background: '#1c1d25',
                  }
            }
          >
            {user.role}
          </span>
        )}

        {/* User avatar + name */}
        {user && (
          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 font-mono text-xs font-semibold"
              style={{
                background: 'rgba(177,54,30,0.15)',
                border: '1px solid rgba(177,54,30,0.3)',
                color: '#b1361e',
              }}
            >
              {initials}
            </div>
            <span className="text-sm hidden lg:block max-w-[140px] truncate" style={{ color: '#7e8088' }}>
              {user.full_name ?? user.email}
            </span>
          </div>
        )}

        <button
          onClick={handleLogout}
          className="text-xs font-medium transition-colors px-2.5 py-1.5 rounded border"
          style={{
            color: '#7e8088',
            borderColor: 'transparent',
            background: 'transparent',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.color = '#dddfe4';
            (e.currentTarget as HTMLButtonElement).style.background = '#252630';
            (e.currentTarget as HTMLButtonElement).style.borderColor = '#2d2e3a';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.color = '#7e8088';
            (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
            (e.currentTarget as HTMLButtonElement).style.borderColor = 'transparent';
          }}
        >
          Sign out
        </button>
      </div>
    </header>
  );
}
