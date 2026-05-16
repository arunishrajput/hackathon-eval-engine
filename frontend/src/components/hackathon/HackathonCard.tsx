import Link from 'next/link';
import type { Hackathon } from '@/lib/types';

interface Props {
  hackathon: Hackathon;
  role: 'admin' | 'participant';
  /** Whether the current user has already joined/submitted */
  joined?: boolean;
  /** Link to use for "View Status" (participant with submission) */
  submissionId?: string;
}

const STATUS_STYLES: Record<string, string> = {
  draft: 'bg-[#252630] text-[#7e8088] border border-[#3a3b48]',
  active: 'bg-emerald-900/30 text-emerald-400 border border-emerald-800/40',
  evaluating: 'bg-yellow-900/30 text-yellow-400 border border-yellow-800/40',
  finalized: 'bg-[rgba(177,54,30,0.12)] text-[#b1361e] border border-[rgba(177,54,30,0.3)]',
};

const STATUS_LABELS: Record<string, string> = {
  draft: 'Draft',
  active: 'Active',
  evaluating: 'Evaluating',
  finalized: 'Finalized',
};

function formatDate(iso?: string): string {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function HackathonCard({ hackathon, role, joined, submissionId }: Props) {
  const adminHref = `/admin/hackathons/${hackathon.id}`;
  const submitHref = `/participant/submit/${hackathon.id}`;
  const statusHref = submissionId ? `/participant/evaluation/${submissionId}` : submitHref;

  return (
    <div className="bg-[#1c1d25] border border-[#2d2e3a] hover:border-[#3a3b48] rounded-xl p-5 flex flex-col gap-4 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-white text-base leading-snug line-clamp-2 flex-1 pr-1">
          {hackathon.title}
        </h3>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {joined && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[rgba(177,54,30,0.12)] text-[#b1361e] border border-[rgba(177,54,30,0.3)] uppercase tracking-wide">
              Joined
            </span>
          )}
          <span
            className={`px-2 py-0.5 rounded text-xs font-medium ${
              STATUS_STYLES[hackathon.status] ?? STATUS_STYLES.draft
            }`}
          >
            {STATUS_LABELS[hackathon.status] ?? hackathon.status}
          </span>
        </div>
      </div>

      {/* Description */}
      {hackathon.description && (
        <p className="text-[#7e8088] text-sm line-clamp-2 leading-relaxed flex-1">
          {hackathon.description}
        </p>
      )}

      {/* Meta row */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#5a5c66]">
        {hackathon.end_date && (
          <span className="flex items-center gap-1">
            <svg
              className="w-3.5 h-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5"
              />
            </svg>
            Ends {formatDate(hackathon.end_date)}
          </span>
        )}
        {hackathon.start_date && !hackathon.end_date && (
          <span>Starts {formatDate(hackathon.start_date)}</span>
        )}
        <span className="w-1 h-1 rounded-full bg-[#2a2a2a]" />
        <span>{hackathon.criteria?.length ?? 0} criteria</span>
        <span className="w-1 h-1 rounded-full bg-[#2a2a2a]" />
        <span>Max {hackathon.max_submissions}</span>
      </div>

      {/* Action button */}
      {role === 'admin' ? (
        <Link
          href={adminHref}
          className="block text-center py-2 px-4 bg-[#b1361e] hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors mt-auto"
        >
          Manage
        </Link>
      ) : joined ? (
        <Link
          href={statusHref}
          className="block text-center py-2 px-4 bg-[#1c1d25] border border-[#3a3b48] hover:border-[#b1361e]/50 text-[#dddfe4] hover:text-white rounded-lg text-sm font-medium transition-colors mt-auto"
        >
          View Status
        </Link>
      ) : hackathon.status === 'active' ? (
        <Link
          href={submitHref}
          className="block text-center py-2 px-4 bg-[#b1361e] hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors mt-auto"
        >
          Submit Project
        </Link>
      ) : (
        <div className="py-2 px-4 bg-[#13141a] border border-[#1a1a1a] text-[#5a5c66] rounded-lg text-sm font-medium text-center mt-auto cursor-not-allowed">
          {hackathon.status === 'finalized' ? 'View Leaderboard' : 'Not accepting submissions'}
        </div>
      )}
    </div>
  );
}
