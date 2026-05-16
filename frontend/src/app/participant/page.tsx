'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth';
import { submissionApi } from '@/lib/api';
import type { Submission } from '@/lib/types';

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-[#252630] text-[#7e8088] border border-[#3a3b48]',
  cloning: 'bg-yellow-900/30 text-yellow-400 border border-yellow-800/40',
  analyzing: 'bg-[rgba(177,54,30,0.12)] text-[#b1361e] border border-[rgba(177,54,30,0.3)]',
  evaluating: 'bg-purple-900/30 text-purple-400 border border-purple-800/40',
  completed: 'bg-emerald-900/30 text-emerald-400 border border-emerald-800/40',
  failed: 'bg-red-900/30 text-red-400 border border-red-800/40',
};

export default function ParticipantDashboard() {
  const { user } = useAuthStore();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [retrying, setRetrying] = useState<string | null>(null);

  const loadSubmissions = () =>
    submissionApi
      .list()
      .then(setSubmissions)
      .catch(() => setSubmissions([]))
      .finally(() => setLoading(false));

  useEffect(() => { loadSubmissions(); }, []);

  const handleRetry = async (id: string) => {
    setRetrying(id);
    try {
      await submissionApi.retry(id);
      await loadSubmissions();
    } catch {
      // ignore — submission list will still refresh
    } finally {
      setRetrying(null);
    }
  };

  const inProgress = submissions.filter(
    (s) => !['completed', 'failed'].includes(s.status)
  );
  const completed = submissions.filter((s) => s.status === 'completed');
  const failed = submissions.filter((s) => s.status === 'failed');

  const displayName = user?.full_name ?? user?.email ?? 'Participant';

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          Welcome back,{' '}
          <span className="text-[#b1361e]">
            {displayName.includes('@') ? displayName.split('@')[0] : displayName}
          </span>
        </h1>
        <p className="text-[#7e8088] text-sm mt-1">
          Submit your project and get AI-powered evaluation feedback
        </p>
      </div>

      {/* Quick stats */}
      {!loading && submissions.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl px-4 py-4">
            <p className="text-xs text-[#7e8088] uppercase tracking-wide mb-1">Submissions</p>
            <p className="text-2xl font-bold text-gray-200 font-mono">{submissions.length}</p>
          </div>
          <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl px-4 py-4">
            <p className="text-xs text-[#7e8088] uppercase tracking-wide mb-1">Completed</p>
            <p className="text-2xl font-bold text-emerald-400 font-mono">{completed.length}</p>
          </div>
          <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl px-4 py-4">
            <p className="text-xs text-[#7e8088] uppercase tracking-wide mb-1">In Progress</p>
            <p className="text-2xl font-bold text-yellow-400 font-mono">{inProgress.length}</p>
          </div>
        </div>
      )}

      {/* Quick links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Link
          href="/participant/hackathons"
          className="bg-[#1c1d25] border border-[#2d2e3a] hover:border-[#b1361e] rounded-xl p-6 transition-colors group"
        >
          <div className="w-9 h-9 rounded-lg bg-[rgba(177,54,30,0.18)] border border-[rgba(177,54,30,0.2)] flex items-center justify-center text-[#b1361e] mb-4">
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M7.73 9.728a6.726 6.726 0 002.748 1.35m8.272-6.842V4.5c0 2.108-.966 3.99-2.48 5.228m2.48-5.492a46.32 46.32 0 012.916.52 6.003 6.003 0 01-5.395 4.972m0 0a6.726 6.726 0 01-2.749 1.35m0 0a6.772 6.772 0 01-3.044 0"
              />
            </svg>
          </div>
          <h2 className="font-semibold text-white text-base mb-1.5">Browse Hackathons</h2>
          <p className="text-[#7e8088] text-sm">
            Find active hackathons and submit your project
          </p>
        </Link>

        <Link
          href="/participant/hackathons"
          className="bg-[#1c1d25] border border-[#2d2e3a] hover:border-[#3a3b48] rounded-xl p-6 transition-colors"
        >
          <div className="w-9 h-9 rounded-lg bg-[#252630] border border-[#3a3b48] flex items-center justify-center text-[#7e8088] mb-4">
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
              />
            </svg>
          </div>
          <h2 className="font-semibold text-white text-base mb-1.5">My Submissions</h2>
          <p className="text-[#7e8088] text-sm">
            Track evaluation status and see scores
          </p>
        </Link>

        <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-6">
          <div className="w-9 h-9 rounded-lg bg-[#252630] border border-[#3a3b48] flex items-center justify-center text-[#7e8088] mb-4">
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"
              />
            </svg>
          </div>
          <h2 className="font-semibold text-white text-base mb-1.5">AI Mentor</h2>
          <p className="text-[#7e8088] text-sm">
            Get personalized improvement suggestions after evaluation
          </p>
        </div>
      </div>

      {/* My submissions */}
      <div>
        <h2 className="text-base font-semibold text-[#dddfe4] mb-3">My Submissions</h2>

        {loading ? (
          <div className="flex items-center justify-center py-10">
            <span className="w-6 h-6 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          </div>
        ) : submissions.length === 0 ? (
          <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl py-10 text-center">
            <p className="text-[#9a9ba8] text-sm">No submissions yet</p>
            <Link
              href="/participant/hackathons"
              className="inline-block mt-3 text-sm text-[#b1361e] hover:text-[#e87060] transition-colors"
            >
              Browse hackathons to get started
            </Link>
          </div>
        ) : (
          <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl overflow-hidden">
            {/* In-progress banner */}
            {inProgress.length > 0 && (
              <div className="px-5 py-2.5 bg-yellow-900/10 border-b border-yellow-800/20 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
                <span className="text-xs text-yellow-400 font-medium">
                  {inProgress.length} evaluation{inProgress.length !== 1 ? 's' : ''} in progress
                </span>
              </div>
            )}
            <table className="w-full">
              <thead>
                <tr className="bg-[#13141a] border-b border-[#2d2e3a]">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                    Repository
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide hidden md:table-cell">
                    Submitted
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {submissions.map((s) => (
                  <tr key={s.id} className="hover:bg-[#1e1f27] transition-colors">
                    <td className="px-4 py-3">
                      <div className="text-sm text-[#dddfe4] font-medium">
                        {s.repo_name ?? s.repo_url.replace('https://github.com/', '')}
                      </div>
                      {s.repo_description && (
                        <div className="text-xs text-[#5a5c66] mt-0.5 line-clamp-1">
                          {s.repo_description}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          STATUS_STYLES[s.status] ?? STATUS_STYLES.pending
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-[#7e8088] hidden md:table-cell">
                      {new Date(s.submitted_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>
                    <td className="px-4 py-3 text-right flex items-center justify-end gap-2">
                      {s.status === 'failed' && (
                        <button
                          onClick={() => handleRetry(s.id)}
                          disabled={retrying === s.id}
                          className="text-xs text-red-400 hover:text-red-300 border border-red-800/40 hover:border-red-700 px-2.5 py-1.5 rounded-lg transition-colors disabled:opacity-50"
                        >
                          {retrying === s.id ? 'Retrying…' : 'Retry'}
                        </button>
                      )}
                      <Link
                        href={`/participant/evaluation/${s.id}`}
                        className="text-xs text-[#b1361e] hover:text-[#e87060] border border-[#3a3b48] hover:border-[#b1361e] px-2.5 py-1.5 rounded-lg transition-colors"
                      >
                        {s.status === 'completed' ? 'View Results' : 'Track'}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Failed submissions notice */}
      {failed.length > 0 && (
        <div className="bg-red-900/20 border border-red-800/40 rounded-xl px-5 py-4">
          <p className="text-sm text-red-400 font-medium mb-1">
            {failed.length} submission{failed.length !== 1 ? 's' : ''} failed evaluation
          </p>
          <p className="text-xs text-red-500/70">
            Check the evaluation page for details and consider resubmitting.
          </p>
        </div>
      )}
    </div>
  );
}
