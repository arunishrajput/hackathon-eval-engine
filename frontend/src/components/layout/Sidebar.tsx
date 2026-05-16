'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { clsx } from 'clsx';

interface NavItem {
  label: string;
  href: string;
  icon?: React.ReactNode;
}

const adminNav: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/admin',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
      </svg>
    ),
  },
  {
    label: 'New Hackathon',
    href: '/admin/hackathons/new',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
      </svg>
    ),
  },
];

const participantNav: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/participant',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
      </svg>
    ),
  },
  {
    label: 'Hackathons',
    href: '/participant/hackathons',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M7.73 9.728a6.726 6.726 0 002.748 1.35m8.272-6.842V4.5c0 2.108-.966 3.99-2.48 5.228m2.48-5.492a46.32 46.32 0 012.916.52 6.003 6.003 0 01-5.395 4.972m0 0a6.726 6.726 0 01-2.749 1.35m0 0a6.772 6.772 0 01-3.044 0" />
      </svg>
    ),
  },
];

export function Sidebar({ role }: { role: 'admin' | 'participant' }) {
  const pathname = usePathname();
  const navItems = role === 'admin' ? adminNav : participantNav;

  return (
    <aside className="w-56 bg-[#13141a] border-r border-[#2d2e3a] flex flex-col flex-shrink-0">
      {/* Logo / brand */}
      <div className="px-4 py-4 border-b border-[#2d2e3a]">
        <div className="flex items-center gap-2.5 mb-3">
          {/* Red square logo mark */}
          <div className="w-7 h-7 rounded bg-[#b1361e] flex items-center justify-center flex-shrink-0 shadow-glow-sm">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <span className="text-sm font-bold tracking-tight block leading-none" style={{ color: '#dddfe4' }}>
              EVAL
              <span style={{ color: '#b1361e' }}>ON</span>
            </span>
            <span className="text-[9px] font-medium tracking-widest uppercase mt-0.5 block" style={{ color: '#5a5c66' }}>
              eval engine
            </span>
          </div>
        </div>

        {/* Role badge */}
        <div
          className={clsx(
            'inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded',
            role === 'admin'
              ? 'bg-purple-900/30 text-purple-400 border border-purple-800/40'
              : 'bg-[#1c1d25] text-[#7e8088] border border-[#2d2e3a]'
          )}
        >
          <span
            className={clsx(
              'w-1.5 h-1.5 rounded-full',
              role === 'admin' ? 'bg-purple-400' : 'bg-[#7e8088]'
            )}
          />
          {role}
        </div>
      </div>

      <nav className="flex-1 py-3">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                'flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-colors relative',
                isActive
                  ? 'bg-[#252630] text-[#dddfe4] border-l-[3px] border-[#b1361e] pl-[13px]'
                  : 'text-[#7e8088] hover:bg-[#1e1f27] hover:text-[#dddfe4] border-l-[3px] border-transparent pl-[13px]'
              )}
            >
              {item.icon && (
                <span
                  className={clsx(
                    'flex-shrink-0',
                    isActive ? 'text-[#b1361e]' : 'text-[#5a5c66]'
                  )}
                >
                  {item.icon}
                </span>
              )}
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom footer */}
      <div className="px-4 py-3 border-t border-[#2d2e3a]">
        <p className="text-[10px] font-mono" style={{ color: '#5a5c66' }}>v1.0.0-mvp</p>
      </div>
    </aside>
  );
}
