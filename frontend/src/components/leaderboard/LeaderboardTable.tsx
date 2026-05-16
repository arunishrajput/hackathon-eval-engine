import type { LeaderboardResponse } from '@/lib/types';

interface Props {
  leaderboard: LeaderboardResponse;
  /** submission_id of the current user to highlight */
  highlightSubmissionId?: string;
}

function TrophyIcon({ rank }: { rank: number }) {
  if (rank === 1) {
    return (
      <svg className="w-4 h-4 text-yellow-400 inline-block mr-1" viewBox="0 0 24 24" fill="currentColor">
        <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
      </svg>
    );
  }
  if (rank === 2) {
    return (
      <svg className="w-4 h-4 text-[#dddfe4] inline-block mr-1" viewBox="0 0 24 24" fill="currentColor">
        <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
      </svg>
    );
  }
  if (rank === 3) {
    return (
      <svg className="w-4 h-4 text-amber-600 inline-block mr-1" viewBox="0 0 24 24" fill="currentColor">
        <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
      </svg>
    );
  }
  return null;
}

function RankCell({ rank }: { rank: number }) {
  const color =
    rank === 1
      ? 'text-yellow-400'
      : rank === 2
      ? 'text-[#dddfe4]'
      : rank === 3
      ? 'text-amber-600'
      : 'text-[#7e8088]';
  return (
    <span className={`font-mono text-sm font-bold ${color} flex items-center`}>
      <TrophyIcon rank={rank} />
      {rank <= 3 ? `#${rank}` : `#${rank}`}
    </span>
  );
}

function ScoreCell({ score }: { score?: number | null }) {
  if (score == null) return <span className="text-[#5a5c66] font-mono">—</span>;
  const color =
    score >= 8
      ? 'text-emerald-400'
      : score >= 6
      ? 'text-[#b1361e]'
      : score >= 4
      ? 'text-yellow-400'
      : 'text-red-400';
  return (
    <span className={`font-mono font-bold text-sm ${color}`}>{score.toFixed(2)}</span>
  );
}

function PercentileBadge({ percentile }: { percentile?: number | null }) {
  if (percentile == null) return <span className="text-[#5a5c66]">—</span>;
  const color =
    percentile >= 90
      ? 'bg-emerald-900/40 text-emerald-400 border-emerald-800/50'
      : percentile >= 70
      ? 'bg-[rgba(177,54,30,0.18)] text-[#b1361e] border-[rgba(177,54,30,0.35)]'
      : percentile >= 50
      ? 'bg-yellow-900/40 text-yellow-400 border-yellow-800/50'
      : 'bg-[#252630] text-[#7e8088] border-[#3a3b48]';
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold border ${color}`}>
      Top {(100 - percentile).toFixed(0)}%
    </span>
  );
}

export function LeaderboardTable({ leaderboard, highlightSubmissionId }: Props) {
  const { entries, total_submissions } = leaderboard;

  return (
    <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl overflow-hidden">
      <div className="px-5 py-3.5 border-b border-[#2d2e3a] flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[#dddfe4]">
          Rankings
          {leaderboard.finalized && (
            <span className="ml-2 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-900/30 text-emerald-400 border border-emerald-800/40 uppercase tracking-wide">
              Final
            </span>
          )}
        </h2>
        <span className="text-xs text-[#7e8088]">
          {total_submissions} submission{total_submissions !== 1 ? 's' : ''}
        </span>
      </div>

      {entries.length === 0 ? (
        <div className="text-center py-12 text-[#7e8088] text-sm">No rankings yet</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-[#13141a] border-b border-[#2d2e3a]">
                <th className="px-4 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide w-16">
                  Rank
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                  Project
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                  Participant
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                  Score
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                  Percentile
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1a1a1a]">
              {entries.map((entry) => {
                const isHighlighted =
                  highlightSubmissionId &&
                  entry.submission_id === highlightSubmissionId;
                return (
                  <tr
                    key={entry.submission_id}
                    className={`transition-colors ${
                      isHighlighted
                        ? 'bg-[rgba(177,54,30,0.10)] border-l-2 border-[#b1361e]'
                        : entry.rank <= 3
                        ? 'bg-yellow-900/5 hover:bg-yellow-900/10'
                        : 'hover:bg-[#1e1f27]'
                    }`}
                  >
                    <td className="px-4 py-3">
                      <RankCell rank={entry.rank} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-[#dddfe4] font-medium">
                        {entry.repo_name ?? (
                          <span className="text-[#5a5c66] font-normal italic">Unnamed</span>
                        )}
                      </div>
                      {entry.repo_url && (
                        <a
                          href={entry.repo_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-[#5a5c66] hover:text-[#b1361e] transition-colors font-mono truncate block max-w-[180px]"
                        >
                          {entry.repo_url.replace('https://github.com/', '')}
                        </a>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-[#9a9ba8]">
                      {isHighlighted ? (
                        <span className="text-[#b1361e] font-semibold">
                          {entry.user_full_name ?? 'You'}
                          <span className="ml-1.5 text-[10px] bg-[rgba(177,54,30,0.18)] border border-[rgba(177,54,30,0.35)] px-1.5 py-0.5 rounded text-[#e87060] font-normal">
                            You
                          </span>
                        </span>
                      ) : (
                        entry.user_full_name ?? (
                          <span className="text-[#5a5c66] italic">Anonymous</span>
                        )
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <ScoreCell score={entry.final_score} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <PercentileBadge percentile={entry.percentile} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
