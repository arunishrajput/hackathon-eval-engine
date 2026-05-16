'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { hackathonApi, adminApi } from '@/lib/api';
import type { Hackathon, Submission } from '@/lib/types';

const STATUS_STYLES: Record<string, string> = {
  draft: 'bg-[#252630] text-[#7e8088] border border-[#3a3b48]',
  active: 'bg-emerald-900/30 text-emerald-400 border border-emerald-800/40',
  evaluating: 'bg-yellow-900/30 text-yellow-400 border border-yellow-800/40',
  finalized: 'bg-[rgba(177,54,30,0.12)] text-[#b1361e] border border-[rgba(177,54,30,0.3)]',
};

const SUBMISSION_STATUS_STYLES: Record<string, string> = {
  pending: 'bg-[#252630] text-[#7e8088] border border-[#3a3b48]',
  cloning: 'bg-yellow-900/30 text-yellow-400 border border-yellow-800/40',
  analyzing: 'bg-[rgba(177,54,30,0.12)] text-[#b1361e] border border-[rgba(177,54,30,0.3)]',
  evaluating: 'bg-purple-900/30 text-purple-400 border border-purple-800/40',
  completed: 'bg-emerald-900/30 text-emerald-400 border border-emerald-800/40',
  failed: 'bg-red-900/30 text-red-400 border border-red-800/40',
};

// Allowed status transitions
const TRANSITIONS: Record<string, { label: string; next: string }> = {
  draft: { label: 'Activate', next: 'active' },
  active: { label: 'Start Evaluating', next: 'evaluating' },
  evaluating: { label: 'Mark Finalized', next: 'finalized' },
};

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl px-4 py-4">
      <p className="text-xs text-[#7e8088] uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-3xl font-bold font-mono ${color}`}>{value}</p>
    </div>
  );
}

export default function HackathonDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [hackathon, setHackathon] = useState<Hackathon | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [transitioning, setTransitioning] = useState(false);
  const [finalizing, setFinalizing] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    const [h, subs] = await Promise.allSettled([
      hackathonApi.get(id),
      adminApi.listSubmissions(id),
    ]);
    if (h.status === 'fulfilled') setHackathon(h.value);
    if (subs.status === 'fulfilled') setSubmissions(subs.value);
    setLoading(false);
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // Auto-refresh every 10 seconds when evaluating
  useEffect(() => {
    if (!hackathon || hackathon.status !== 'evaluating') return;
    const timer = setInterval(load, 10000);
    return () => clearInterval(timer);
  }, [hackathon, load]);

  const handleTransition = async () => {
    if (!id || !hackathon) return;
    const transition = TRANSITIONS[hackathon.status];
    if (!transition) return;
    if (
      !window.confirm(
        `Transition status from "${hackathon.status}" to "${transition.next}"?`
      )
    )
      return;
    setTransitioning(true);
    try {
      await adminApi.transitionStatus(id, transition.next);
      await load();
    } catch {
      // ignore
    } finally {
      setTransitioning(false);
    }
  };

  const handleFinalize = async () => {
    if (!id) return;
    if (!window.confirm('Finalize rankings? This will lock all scores and make them public.'))
      return;
    setFinalizing(true);
    try {
      await adminApi.finalizeRankings(id);
      await load();
    } catch {
      // ignore
    } finally {
      setFinalizing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <span className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (!hackathon) {
    return <div className="text-center py-16 text-red-400">Hackathon not found</div>;
  }

  const counts = {
    total: submissions.length,
    evaluating: submissions.filter((s) =>
      ['cloning', 'analyzing', 'evaluating'].includes(s.status)
    ).length,
    completed: submissions.filter((s) => s.status === 'completed').length,
    failed: submissions.filter((s) => s.status === 'failed').length,
  };

  const allDone =
    submissions.length > 0 &&
    submissions.every((s) => s.status === 'completed' || s.status === 'failed');

  const transition = TRANSITIONS[hackathon.status];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/admin"
              className="text-xs text-[#5a5c66] hover:text-[#9a9ba8] transition-colors"
            >
              Dashboard
            </Link>
            <span className="text-gray-700">/</span>
            <span className="text-xs text-[#7e8088]">{hackathon.title}</span>
          </div>
          <h1 className="text-2xl font-bold text-white">{hackathon.title}</h1>
          <div className="flex items-center gap-2 mt-2">
            <span
              className={`inline-block px-2.5 py-0.5 rounded text-xs font-medium ${
                STATUS_STYLES[hackathon.status] ?? STATUS_STYLES.draft
              }`}
            >
              {hackathon.status}
            </span>
            {hackathon.start_date && (
              <span className="text-xs text-[#7e8088]">
                {new Date(hackathon.start_date).toLocaleDateString()}
                {hackathon.end_date &&
                  ` — ${new Date(hackathon.end_date).toLocaleDateString()}`}
              </span>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {transition && (
            <button
              onClick={handleTransition}
              disabled={transitioning}
              className="px-4 py-2 bg-[#b1361e] hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {transitioning && (
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              )}
              {transition.label}
            </button>
          )}
          {hackathon.status === 'evaluating' && allDone && (
            <button
              onClick={handleFinalize}
              disabled={finalizing}
              className="px-4 py-2 bg-emerald-700 hover:bg-emerald-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {finalizing && (
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              )}
              Finalize Rankings
            </button>
          )}
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Total" value={counts.total} color="text-gray-200" />
        <StatCard label="In Progress" value={counts.evaluating} color="text-yellow-400" />
        <StatCard label="Completed" value={counts.completed} color="text-emerald-400" />
        <StatCard label="Failed" value={counts.failed} color="text-red-400" />
      </div>

      {/* Quick nav */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          href={`/admin/hackathons/${id}/criteria`}
          className="bg-[#1c1d25] border border-[#2d2e3a] hover:border-[#3a3b48] rounded-xl p-5 transition-colors"
        >
          <div className="w-8 h-8 rounded-lg bg-purple-900/30 border border-purple-800/30 flex items-center justify-center text-purple-400 mb-3">
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
              />
            </svg>
          </div>
          <h3 className="font-semibold text-white mb-1">Criteria</h3>
          <p className="text-sm text-[#7e8088]">
            {hackathon.criteria?.length ?? 0} defined — Edit weights
          </p>
        </Link>

        <Link
          href={`/admin/hackathons/${id}/submissions`}
          className="bg-[#1c1d25] border border-[#2d2e3a] hover:border-[#3a3b48] rounded-xl p-5 transition-colors"
        >
          <div className="w-8 h-8 rounded-lg bg-[rgba(177,54,30,0.12)] border border-[rgba(177,54,30,0.2)] flex items-center justify-center text-[#b1361e] mb-3">
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
              />
            </svg>
          </div>
          <h3 className="font-semibold text-white mb-1">Submissions</h3>
          <p className="text-sm text-[#7e8088]">{counts.total} total submissions</p>
        </Link>

        <Link
          href={`/admin/hackathons/${id}/rankings`}
          className="bg-[#1c1d25] border border-[#2d2e3a] hover:border-[#3a3b48] rounded-xl p-5 transition-colors"
        >
          <div className="w-8 h-8 rounded-lg bg-emerald-900/30 border border-emerald-800/30 flex items-center justify-center text-emerald-400 mb-3">
            <svg
              className="w-4 h-4"
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
          <h3 className="font-semibold text-white mb-1">Rankings</h3>
          <p className="text-sm text-[#7e8088]">Manage &amp; finalize scores</p>
        </Link>
      </div>

      {/* Submissions table */}
      {submissions.length > 0 && (
        <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl overflow-hidden">
          <div className="px-5 py-3.5 border-b border-[#2d2e3a] flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[#dddfe4]">Recent Submissions</h2>
            {hackathon.status === 'evaluating' && (
              <span className="text-xs text-[#5a5c66]">Auto-refreshing every 10s</span>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-[#13141a] border-b border-[#2d2e3a]">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                    Repository
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide hidden md:table-cell">
                    Participant
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                    Status
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {submissions.slice(0, 20).map((s) => (
                  <tr key={s.id} className="hover:bg-[#1e1f27] transition-colors">
                    <td className="px-4 py-3">
                      <a
                        href={s.repo_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#b1361e] hover:text-[#e87060] text-sm transition-colors font-mono"
                      >
                        {s.repo_url.replace('https://github.com/', '')}
                      </a>
                    </td>
                    <td className="px-4 py-3 text-sm text-[#7e8088] hidden md:table-cell">
                      {s.user_id.slice(0, 8)}…
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          SUBMISSION_STATUS_STYLES[s.status] ??
                          SUBMISSION_STATUS_STYLES.pending
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        href={`/participant/evaluation/${s.id}`}
                        className="text-xs text-[#b1361e] hover:text-[#e87060] transition-colors border border-[#3a3b48] hover:border-[#b1361e] px-2.5 py-1 rounded"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {submissions.length > 20 && (
            <div className="px-5 py-3 border-t border-[#2d2e3a] text-center">
              <Link
                href={`/admin/hackathons/${id}/submissions`}
                className="text-sm text-[#b1361e] hover:text-[#e87060] transition-colors"
              >
                View all {submissions.length} submissions
              </Link>
            </div>
          )}
        </div>
      )}

      {hackathon.description && (
        <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-6">
          <h2 className="text-xs font-semibold text-[#7e8088] uppercase tracking-wide mb-3">
            Description
          </h2>
          <p className="text-[#9a9ba8] leading-relaxed text-sm">{hackathon.description}</p>
        </div>
      )}
    </div>
  );
}
