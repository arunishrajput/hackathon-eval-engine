'use client';

import { useState } from 'react';
import { AgentResultCard } from './AgentResultCard';
import { EvidenceList } from './EvidenceList';
import type { Evaluation } from '@/lib/types';

interface Props {
  evaluation: Evaluation;
}

type TabId = 'overview' | 'agents' | 'recommendations';

const TABS: { id: TabId; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'agents', label: 'Agent Details' },
  { id: 'recommendations', label: 'Recommendations' },
];

function MetaStat({ label, value }: { label: string; value: string | number | boolean }) {
  const display =
    typeof value === 'boolean' ? (
      <span className={value ? 'text-emerald-400' : 'text-red-400'}>
        {value ? 'Yes' : 'No'}
      </span>
    ) : (
      <span className="text-white">{value}</span>
    );

  return (
    <div className="bg-[#13141a] border border-[#1a1a1a] rounded-lg px-4 py-3">
      <p className="text-xs text-[#7e8088] uppercase tracking-wide mb-1">{label}</p>
      <p className="text-sm font-semibold">{display}</p>
    </div>
  );
}

export function ReportViewer({ evaluation }: Props) {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const report = evaluation.report;

  return (
    <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl overflow-hidden">
      {/* Tab bar */}
      <div className="flex border-b border-[#2d2e3a]">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'text-brand-400 border-b-2 border-brand-500 bg-[#13141a]'
                : 'text-[#7e8088] hover:text-[#dddfe4] hover:bg-[#1e1f27]'
            }`}
          >
            {tab.label}
            {tab.id === 'agents' && evaluation.agent_results?.length > 0 && (
              <span className="ml-2 text-xs bg-[#252630] border border-[#3a3b48] text-[#7e8088] px-1.5 py-0.5 rounded-full">
                {evaluation.agent_results.length}
              </span>
            )}
          </button>
        ))}
      </div>

      <div className="p-6">
        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {report?.summary && (
              <p className="text-[#9a9ba8] text-sm leading-relaxed">{report.summary}</p>
            )}

            {report?.metadata && (
              <div>
                <h3 className="text-xs font-semibold text-[#7e8088] uppercase tracking-wider mb-3">
                  Repository Metadata
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <MetaStat label="Total Files" value={report.metadata.total_files ?? 0} />
                  <MetaStat
                    label="Lines of Code"
                    value={(report.metadata.total_lines ?? 0).toLocaleString()}
                  />
                  <MetaStat label="Has Tests" value={report.metadata.has_tests ?? false} />
                  <MetaStat label="Has Docker" value={report.metadata.has_docker ?? false} />
                </div>
                {report.metadata.languages && report.metadata.languages.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {report.metadata.languages.map((lang) => (
                      <span
                        key={lang}
                        className="px-2.5 py-1 bg-[#13141a] border border-[#3a3b48] rounded text-xs text-[#9a9ba8] font-mono"
                      >
                        {lang}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {report && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <EvidenceList
                  items={report.top_strengths ?? []}
                  title="Top Strengths"
                  type="strength"
                />
                <EvidenceList
                  items={report.top_weaknesses ?? []}
                  title="Areas to Improve"
                  type="weakness"
                />
              </div>
            )}
          </div>
        )}

        {/* AGENTS TAB */}
        {activeTab === 'agents' && (
          <div>
            {evaluation.agent_results && evaluation.agent_results.length > 0 ? (
              <div className="space-y-3">
                {evaluation.agent_results.map((r) => (
                  <AgentResultCard key={r.id} result={r} />
                ))}
              </div>
            ) : (
              <p className="text-[#7e8088] text-sm text-center py-8">
                No agent results available.
              </p>
            )}
          </div>
        )}

        {/* RECOMMENDATIONS TAB */}
        {activeTab === 'recommendations' && (
          <div>
            {report?.recommendations && report.recommendations.length > 0 ? (
              <div className="space-y-3">
                {report.recommendations.map((rec, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 bg-[#13141a] border border-[#1a1a1a] rounded-lg px-4 py-3"
                  >
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-brand-900/50 border border-brand-800/50 flex items-center justify-center text-xs text-brand-400 font-bold mt-0.5">
                      {i + 1}
                    </span>
                    <p className="text-sm text-[#dddfe4] leading-relaxed">{rec}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[#7e8088] text-sm text-center py-8">
                No recommendations available yet.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
