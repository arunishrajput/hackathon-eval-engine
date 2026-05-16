'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { adminApi } from '@/lib/api';
import type { Submission } from '@/lib/types';

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-[#252630] text-[#7e8088] border border-[#3a3b48]',
  cloning: 'bg-yellow-900/30 text-yellow-400 border border-yellow-800/40',
  analyzing: 'bg-[rgba(177,54,30,0.12)] text-[#b1361e] border border-[rgba(177,54,30,0.3)]',
  evaluating: 'bg-purple-900/30 text-purple-400 border border-purple-800/40',
  completed: 'bg-emerald-900/30 text-emerald-400 border border-emerald-800/40',
  failed: 'bg-red-900/30 text-red-400 border border-red-800/40',
};

const ALL_STATUSES = ['all', 'pending', 'cloning', 'analyzing', 'evaluating', 'completed', 'failed'] as const;
type StatusFilter = (typeof ALL_STATUSES)[number];

export default function AdminSubmissionsPage() {
  const { id } = useParams<{ id: string }>();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<StatusFilter>('all');

  useEffect(() => {
    if (id) {
      adminApi
        .listSubmissions(id)
        .then(setSubmissions)
        .finally(() => setLoading(false));
    }
  }, [id]);

  const filtered =
    filter === 'all' ? submissions : submissions.filter((s) => s.status === filter);

  const countFor = (status: string) =>
    status === 'all'
      ? submissions.length
      : submissions.filter((s) => s.status === status).length;

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href={`/admin/hackathons/${id}`}
              className="text-xs text-[#5a5c66] hover:text-[#9a9ba8] transition-colors"
            >
              Hackathon
            </Link>
            <span className="text-gray-700">/</span>
            <span className="text-xs text-[#7e8088]">Submissions</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Submissions</h1>
          <p className="text-[#7e8088] text-sm mt-0.5">
            All submitted projects for this hackathon
          </p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 mb-4 overflow-x-auto pb-1">
        {ALL_STATUSES.map((s) => {
          const count = countFor(s);
          const active = filter === s;
          return (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap flex items-center gap-1.5 ${
                active
                  ? 'bg-[rgba(177,54,30,0.12)] text-[#b1361e] border border-[rgba(177,54,30,0.3)]'
                  : 'text-[#7e8088] hover:text-[#dddfe4] border border-transparent hover:bg-[#252630]'
              }`}
            >
              <span className="capitalize">{s}</span>
              <span
                className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono ${
                  active ? 'bg-blue-800/40 text-[#e87060]' : 'bg-[#252630] text-[#5a5c66]'
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <span className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        </div>
      ) : (
        <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl overflow-hidden">
          {filtered.length === 0 ? (
            <div className="text-center py-12 text-[#7e8088] text-sm">
              {filter === 'all' ? 'No submissions yet' : `No ${filter} submissions`}
            </div>
          ) : (
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
                {filtered.map((s) => (
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
                      {s.repo_description && (
                        <p className="text-xs text-[#5a5c66] mt-0.5 line-clamp-1">
                          {s.repo_description}
                        </p>
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
                      {s.error_message && (
                        <p className="text-xs text-red-500 mt-0.5 line-clamp-1">
                          {s.error_message}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-[#7e8088] hidden md:table-cell">
                      {new Date(s.submitted_at).toLocaleString(undefined, {
                        dateStyle: 'medium',
                        timeStyle: 'short',
                      })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        href={`/participant/evaluation/${s.id}`}
                        className="text-xs text-[#b1361e] hover:text-[#e87060] transition-colors border border-[#3a3b48] hover:border-[#b1361e] px-2.5 py-1.5 rounded-lg"
                      >
                        View Evaluation
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
