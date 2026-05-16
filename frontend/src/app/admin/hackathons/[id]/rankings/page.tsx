'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { rankingApi, adminApi } from '@/lib/api';
import { LeaderboardTable } from '@/components/leaderboard/LeaderboardTable';
import type { LeaderboardResponse } from '@/lib/types';

function downloadCsv(leaderboard: LeaderboardResponse) {
  const headers = ['Rank', 'Project', 'Participant', 'Score', 'Percentile', 'Repository URL'];
  const rows = leaderboard.entries.map((e) => [
    e.rank,
    e.repo_name ?? '',
    e.user_full_name ?? '',
    e.final_score != null ? e.final_score.toFixed(2) : '',
    e.percentile != null ? e.percentile.toFixed(1) : '',
    e.repo_url ?? '',
  ]);

  const csvContent = [headers, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    .join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `rankings-${leaderboard.hackathon_id}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export default function AdminRankingsPage() {
  const { id } = useParams<{ id: string }>();
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [finalizing, setFinalizing] = useState(false);

  const load = async () => {
    if (!id) return;
    try {
      const data = await rankingApi.getLeaderboard(id);
      setLeaderboard(data);
    } catch {
      // no rankings yet
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleFinalize = async () => {
    if (!id) return;
    if (
      !window.confirm('Finalize rankings? This will lock all scores and make them public.')
    )
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
            <span className="text-xs text-[#7e8088]">Rankings</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Rankings</h1>
          <p className="text-[#7e8088] text-sm mt-0.5">
            Full leaderboard — visible to admins before finalization
          </p>
        </div>

        <div className="flex items-center gap-2">
          {leaderboard && leaderboard.entries.length > 0 && (
            <button
              onClick={() => downloadCsv(leaderboard)}
              className="flex items-center gap-1.5 px-3 py-2 bg-[#1c1d25] border border-[#3a3b48] hover:border-[#4a4b58] text-[#9a9ba8] hover:text-gray-200 rounded-lg text-sm font-medium transition-colors"
            >
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
              Export CSV
            </button>
          )}

          {leaderboard?.finalized ? (
            <span className="px-3 py-1.5 bg-emerald-900/30 border border-emerald-800/40 text-emerald-400 rounded-lg text-sm font-medium">
              Finalized
            </span>
          ) : leaderboard && leaderboard.entries.length > 0 ? (
            <button
              onClick={handleFinalize}
              disabled={finalizing}
              className="px-4 py-2 bg-[#b1361e] hover:bg-blue-500 text-white rounded-lg text-sm font-medium disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {finalizing ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Finalizing...
                </>
              ) : (
                'Finalize Rankings'
              )}
            </button>
          ) : null}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <span className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        </div>
      ) : leaderboard && leaderboard.entries.length > 0 ? (
        <LeaderboardTable leaderboard={leaderboard} />
      ) : (
        <div className="text-center py-16 bg-[#1c1d25] border border-[#2d2e3a] rounded-xl">
          <p className="text-[#9a9ba8] text-sm">No rankings available yet</p>
          <p className="text-[#5a5c66] text-xs mt-1">
            Rankings are computed once submissions are evaluated
          </p>
        </div>
      )}
    </div>
  );
}
