'use client';

import { useState } from 'react';
import type { AgentResult } from '@/lib/types';

interface Props {
  result: AgentResult;
}

const AGENT_LABELS: Record<string, string> = {
  repo_understanding: 'Repository Structure & Documentation',
  code_quality: 'Code Quality',
  innovation: 'Innovation & Creativity',
  comparative: 'Comparative Analysis',
  documentation: 'Documentation',
  testing: 'Testing Coverage',
  security: 'Security Analysis',
};

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 8
      ? 'bg-emerald-900/40 text-emerald-400 border-emerald-800/50'
      : score >= 6
      ? 'bg-brand-900/40 text-brand-400 border-brand-800/50'
      : score >= 4
      ? 'bg-yellow-900/40 text-yellow-400 border-yellow-800/50'
      : 'bg-red-900/40 text-red-400 border-red-800/50';

  return (
    <span className={`px-2.5 py-1 rounded-md border text-sm font-bold font-mono ${color}`}>
      {score.toFixed(1)}
      <span className="text-xs font-normal opacity-70">/10</span>
    </span>
  );
}

export function AgentResultCard({ result }: Props) {
  const [expanded, setExpanded] = useState(false);
  const label = AGENT_LABELS[result.agent_id] ?? result.agent_id;

  if (result.abstained) {
    return (
      <div className="bg-[#1c1d25] border border-red-900/40 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium text-[#9a9ba8]">{label}</h4>
          <span className="text-xs bg-red-900/30 text-red-400 px-2 py-0.5 rounded border border-red-800/50 flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            Model Failed
          </span>
        </div>
        {result.abstain_reason && (
          <p className="text-xs text-[#5a5c66] mt-2 leading-relaxed">{result.abstain_reason}</p>
        )}
      </div>
    );
  }

  return (
    <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-lg overflow-hidden">
      {/* Header row */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-[#1e1f27] transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <h4 className="text-sm font-medium text-gray-200">{label}</h4>
          {result.confidence != null && (
            <span className="text-xs text-[#7e8088] font-mono">
              {(result.confidence * 100).toFixed(0)}% confidence
            </span>
          )}
          {result.processing_time_ms != null && (
            <span className="text-xs text-[#5a5c66] hidden sm:inline">
              {(result.processing_time_ms / 1000).toFixed(1)}s
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          {result.score_raw != null && <ScoreBadge score={result.score_raw} />}
          <svg
            className={`w-4 h-4 text-[#7e8088] transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Expandable body */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-[#1a1a1a] pt-4 space-y-4">
          {result.reasoning && (
            <p className="text-sm text-[#9a9ba8] leading-relaxed">{result.reasoning}</p>
          )}

          {result.evidence && result.evidence.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-[#7e8088] uppercase tracking-wider mb-2">
                Evidence
              </p>
              <ul className="space-y-1">
                {result.evidence.map((e, i) => (
                  <li
                    key={i}
                    className="text-xs text-[#9a9ba8] flex items-start gap-2 font-mono bg-[#13141a] px-2.5 py-1.5 rounded border border-[#1a1a1a]"
                  >
                    <span className="text-brand-500 mt-0.5 flex-shrink-0">&#8250;</span>
                    {e}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {result.strengths && result.strengths.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-emerald-500 uppercase tracking-wider mb-2">
                  Strengths
                </p>
                <ul className="space-y-1">
                  {result.strengths.map((s, i) => (
                    <li key={i} className="text-xs text-[#9a9ba8] flex items-start gap-1.5">
                      <span className="text-emerald-500 mt-0.5 flex-shrink-0">+</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.weaknesses && result.weaknesses.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-2">
                  Weaknesses
                </p>
                <ul className="space-y-1">
                  {result.weaknesses.map((w, i) => (
                    <li key={i} className="text-xs text-[#9a9ba8] flex items-start gap-1.5">
                      <span className="text-red-400 mt-0.5 flex-shrink-0">−</span>
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
