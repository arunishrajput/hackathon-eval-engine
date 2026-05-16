'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { rankingApi, submissionApi } from '@/lib/api';
import { LeaderboardTable } from '@/components/leaderboard/LeaderboardTable';
import { useAuthStore } from '@/store/auth';
import type { LeaderboardResponse, Submission } from '@/lib/types';

export default function LeaderboardPage() {
  const { hackathonId } = useParams<{ hackathonId: string }>();
  const { user } = useAuthStore();
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null);
  const [mySubmission, setMySubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!hackathonId) return;

    Promise.allSettled([
      rankingApi.getLeaderboard(hackathonId),
      submissionApi.list(),
    ]).then(([lbResult, subResult]) => {
      if (lbResult.status === 'fulfilled') setLeaderboard(lbResult.value);
      if (subResult.status === 'fulfilled') {
        const mine = subResult.value.find((s) => s.hackathon_id === hackathonId);
        setMySubmission(mine ?? null);
      }
      setLoading(false);
    });
  }, [hackathonId]);

  // Find the current user's leaderboard entry
  const myEntry = leaderboard?.entries.find(
    (e) => mySubmission && e.submission_id === mySubmission.id
  );

  const showBlocked =
    leaderboard && !leaderboard.finalized && leaderboard.entries.length === 0;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Leaderboard</h1>
          <p className="text-[#7e8088] text-sm mt-0.5">
            Rankings across all evaluated submissions
          </p>
        </div>
        <div className="flex items-center gap-2">
          {leaderboard?.finalized && (
            <span className="px-3 py-1.5 bg-emerald-900/30 border border-emerald-800/40 text-emerald-400 rounded-lg text-sm font-medium">
              Final Results
            </span>
          )}
          <Link
            href="/participant/hackathons"
            className="text-xs text-[#7e8088] hover:text-[#dddfe4] border border-[#3a3b48] hover:border-[#4a4b58] px-3 py-1.5 rounded-lg transition-colors"
          >
            All Hackathons
          </Link>
        </div>
      </div>

      {/* My rank badge */}
      {myEntry && (
        <div className="bg-[rgba(177,54,30,0.10)] border border-[rgba(177,54,30,0.3)] rounded-xl px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-[rgba(177,54,30,0.2)] border border-[rgba(177,54,30,0.35)] flex items-center justify-center text-[#b1361e] font-bold text-sm">
              #{myEntry.rank}
            </div>
            <div>
              <p className="text-sm font-semibold text-white">
                Your Rank: #{myEntry.rank}
                {leaderboard && (
                  <span className="text-[#7e8088] font-normal">
                    {' '}
                    of {leaderboard.total_submissions}
                  </span>
                )}
              </p>
              <p className="text-xs text-[#7e8088] mt-0.5">
                Score:{' '}
                <span className="text-[#b1361e] font-mono font-semibold">
                  {myEntry.final_score?.toFixed(2) ?? '—'}
                </span>
              </p>
            </div>
          </div>
          {myEntry.percentile != null && (
            <div className="text-right">
              <span className="text-sm font-bold text-[#b1361e]">
                Top {(100 - myEntry.percentile).toFixed(0)}%
              </span>
              <p className="text-xs text-[#5a5c66] mt-0.5">Percentile</p>
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <span className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        </div>
      ) : showBlocked ? (
        <div className="text-center py-16 bg-[#1c1d25] border border-[#2d2e3a] rounded-xl">
          <div className="w-12 h-12 rounded-full bg-[#252630] border border-[#3a3b48] flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-6 h-6 text-[#5a5c66]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
              />
            </svg>
          </div>
          <p className="text-[#dddfe4] font-medium mb-1">Rankings not yet available</p>
          <p className="text-[#5a5c66] text-sm">
            The organizer will publish rankings after evaluations are complete.
          </p>
        </div>
      ) : leaderboard && leaderboard.entries.length > 0 ? (
        <LeaderboardTable
          leaderboard={leaderboard}
          highlightSubmissionId={mySubmission?.id}
        />
      ) : (
        <div className="text-center py-16 bg-[#1c1d25] border border-[#2d2e3a] rounded-xl">
          <p className="text-[#9a9ba8] text-sm">No rankings available yet</p>
        </div>
      )}

      {/* Link to mentor if we have a submission */}
      {mySubmission && mySubmission.status === 'completed' && (
        <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl px-5 py-4 flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-white mb-0.5">
              Want to improve your score?
            </p>
            <p className="text-xs text-[#7e8088]">
              Chat with the AI mentor for personalized feedback
            </p>
          </div>
          <Link
            href={`/participant/mentor/${mySubmission.id}`}
            className="px-4 py-2 bg-[#b1361e] hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors flex-shrink-0"
          >
            Open Mentor
          </Link>
        </div>
      )}
    </div>
  );
}
