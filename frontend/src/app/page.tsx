'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth';

const FEATURES = [
  {
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
      </svg>
    ),
    title: 'Multi-Agent AI Evaluation',
    description:
      'Specialized AI agents independently analyze code quality, innovation, documentation, and more — then aggregate into a unified score.',
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
    title: 'Real-Time Progress Streaming',
    description:
      'Watch your evaluation unfold live with SSE-powered stage tracking — from repository cloning through final score aggregation.',
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
    ),
    title: 'AI Mentor Chat',
    description:
      'Get personalized, context-aware feedback on your submission through a RAG-powered AI mentor that knows your codebase.',
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M7.73 9.728a6.726 6.726 0 002.748 1.35m8.272-6.842V4.5c0 2.108-.966 3.99-2.48 5.228m2.48-5.492a46.32 46.32 0 012.916.52 6.003 6.003 0 01-5.395 4.972m0 0a6.726 6.726 0 01-2.749 1.35m0 0a6.772 6.772 0 01-3.044 0" />
      </svg>
    ),
    title: 'Live Leaderboard',
    description:
      'Competitive rankings with percentile scores, normalized across all submissions — finalized by organizers when ready.',
  },
];

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div
      className="rounded-lg p-5 transition-colors group cursor-default"
      style={{
        background: '#1c1d25',
        border: '1px solid #2d2e3a',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = '#b1361e';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = '#2d2e3a';
      }}
    >
      <div
        className="w-9 h-9 rounded flex items-center justify-center mb-4"
        style={{
          background: 'rgba(177,54,30,0.12)',
          border: '1px solid rgba(177,54,30,0.2)',
          color: '#b1361e',
        }}
      >
        {icon}
      </div>
      <h3 className="text-sm font-semibold mb-1.5" style={{ color: '#dddfe4' }}>{title}</h3>
      <p className="text-xs leading-relaxed" style={{ color: '#7e8088' }}>{description}</p>
    </div>
  );
}

export default function LandingPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      router.replace(user?.role === 'admin' ? '/admin' : '/participant');
    }
  }, [isAuthenticated, user, router]);

  if (isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: '#13141a' }}>
        <span className="w-8 h-8 border-2 border-t-[#b1361e] rounded-full animate-spin" style={{ borderColor: 'rgba(177,54,30,0.2)', borderTopColor: '#b1361e' }} />
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: '#13141a', color: '#dddfe4' }}>
      {/* Nav */}
      <nav
        className="sticky top-0 z-10 backdrop-blur-sm"
        style={{ background: 'rgba(19,20,26,0.92)', borderBottom: '1px solid #2d2e3a' }}
      >
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded flex items-center justify-center flex-shrink-0"
              style={{ background: '#b1361e' }}
            >
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
              </svg>
            </div>
            <span className="font-bold tracking-tight text-sm" style={{ color: '#dddfe4' }}>
              EVAL<span style={{ color: '#b1361e' }}>ON</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/auth/login"
              className="text-sm px-3 py-1.5 rounded transition-colors"
              style={{ color: '#7e8088' }}
            >
              Sign in
            </Link>
            <Link
              href="/auth/register"
              className="text-sm px-4 py-1.5 rounded font-semibold transition-colors"
              style={{ background: '#b1361e', color: '#fff' }}
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section
        className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center relative"
        style={{
          backgroundImage:
            'radial-gradient(circle, rgba(45,46,58,0.6) 1px, transparent 1px)',
          backgroundSize: '28px 28px',
        }}
      >
        {/* Terminal-style badge */}
        <div
          className="inline-flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded mb-8"
          style={{
            background: '#1c1d25',
            border: '1px solid #2d2e3a',
            color: '#7e8088',
          }}
        >
          <span style={{ color: '#b1361e' }}>//</span>
          <span>AI-powered evaluation</span>
          <span
            className="w-1.5 h-3 inline-block animate-pulse"
            style={{ background: '#b1361e', borderRadius: '1px' }}
          />
        </div>

        <h1
          className="text-5xl sm:text-6xl font-bold leading-tight tracking-tight mb-5"
          style={{ color: '#dddfe4' }}
        >
          Evaluate hackathons
          <br />
          <span className="text-gradient-brand">with AI precision</span>
        </h1>

        <p className="text-base max-w-2xl mx-auto mb-10 leading-relaxed" style={{ color: '#7e8088' }}>
          Submit your GitHub repository and receive in-depth, multi-dimensional AI evaluation — with real-time
          progress tracking, radar score charts, and an AI mentor to guide your improvement.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/auth/register"
            className="px-8 py-3 rounded font-semibold text-sm transition-colors shadow-glow-brand"
            style={{ background: '#b1361e', color: '#fff' }}
          >
            Start evaluating free
          </Link>
          <Link
            href="/auth/login"
            className="px-8 py-3 rounded font-semibold text-sm transition-colors"
            style={{
              background: '#1c1d25',
              border: '1px solid #2d2e3a',
              color: '#7e8088',
            }}
          >
            Sign in to dashboard
          </Link>
        </div>
      </section>

      {/* Stats strip */}
      <section style={{ borderTop: '1px solid #2d2e3a', borderBottom: '1px solid #2d2e3a', background: '#1c1d25' }}>
        <div className="max-w-6xl mx-auto px-6 py-7 grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
          {[
            { value: '4+', label: 'AI Evaluation Agents' },
            { value: 'SSE', label: 'Real-Time Streaming' },
            { value: 'RAG', label: 'Mentor Chat Engine' },
            { value: '360°', label: 'Code Analysis' },
          ].map((s) => (
            <div key={s.label}>
              <p className="text-2xl font-bold font-mono mb-1" style={{ color: '#b1361e' }}>{s.value}</p>
              <p className="text-xs" style={{ color: '#7e8088' }}>{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-center mb-2" style={{ color: '#dddfe4' }}>
          Everything you need to evaluate code
        </h2>
        <p className="text-sm text-center mb-10 max-w-xl mx-auto" style={{ color: '#7e8088' }}>
          Built for hackathon organizers and participants who want objective, comprehensive, and transparent evaluation.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURES.map((f) => (
            <FeatureCard key={f.title} {...f} />
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-6 pb-16">
        <div
          className="rounded-lg p-10 text-center"
          style={{ background: '#1c1d25', border: '1px solid #2d2e3a' }}
        >
          <h2 className="text-2xl font-bold mb-3" style={{ color: '#dddfe4' }}>
            Ready to evaluate your project?
          </h2>
          <p className="text-sm mb-8 max-w-md mx-auto" style={{ color: '#7e8088' }}>
            Join the platform, submit your GitHub repository, and get AI-powered feedback in minutes.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/auth/register"
              className="px-7 py-2.5 rounded font-semibold text-sm transition-colors"
              style={{ background: '#b1361e', color: '#fff' }}
            >
              Create free account
            </Link>
            <Link
              href="/auth/login"
              className="px-7 py-2.5 rounded font-semibold text-sm transition-colors"
              style={{ border: '1px solid #2d2e3a', color: '#7e8088' }}
            >
              Sign in
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid #2d2e3a' }} className="py-5">
        <div className="max-w-6xl mx-auto px-6 text-center text-xs font-mono" style={{ color: '#5a5c66' }}>
          Hackathon Eval Engine &mdash; AI-powered evaluation platform
        </div>
      </footer>
    </div>
  );
}
