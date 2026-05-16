'use client';

import { useEvaluationStream } from '@/hooks/useEvaluationStream';
import type { Evaluation } from '@/lib/types';

interface Props {
  submissionId: string;
  onComplete: (evaluation: Evaluation) => void;
}

function StageIcon({ status }: { status: 'waiting' | 'active' | 'done' | 'error' }) {
  if (status === 'done') {
    return (
      <span className="w-6 h-6 flex items-center justify-center rounded-full bg-brand-500 text-white text-xs font-bold">
        &#10003;
      </span>
    );
  }
  if (status === 'error') {
    return (
      <span className="w-6 h-6 flex items-center justify-center rounded-full bg-red-500 text-white text-xs font-bold">
        &#10007;
      </span>
    );
  }
  if (status === 'active') {
    return (
      <span className="w-6 h-6 flex items-center justify-center rounded-full border-2 border-brand-500">
        <span className="w-2.5 h-2.5 rounded-full bg-brand-500 animate-pulse" />
      </span>
    );
  }
  return (
    <span className="w-6 h-6 flex items-center justify-center rounded-full border-2 border-[#3a3b48]">
      <span className="w-2 h-2 rounded-full bg-[#333]" />
    </span>
  );
}

export function ProgressStream({ submissionId, onComplete }: Props) {
  const { stages, progress, isFailed, error } = useEvaluationStream(
    submissionId,
    onComplete
  );

  return (
    <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-6">
      {/* Progress bar */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-[#dddfe4] tracking-wide uppercase">
          Evaluation in Progress
        </h3>
        <span className="text-sm font-mono text-brand-400">{progress}%</span>
      </div>
      <div className="w-full bg-[#252630] rounded-full h-1.5 mb-6 overflow-hidden">
        <div
          className={`h-1.5 rounded-full transition-all duration-700 ease-out ${
            isFailed ? 'bg-red-500' : 'bg-gradient-to-r from-brand-600 to-brand-400'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Stage timeline */}
      <div className="space-y-0">
        {stages.map((stage, idx) => (
          <div key={stage.id} className="flex items-stretch gap-4">
            {/* Icon + connector column */}
            <div className="flex flex-col items-center">
              <StageIcon status={stage.status} />
              {idx < stages.length - 1 && (
                <div
                  className={`w-px flex-1 mt-1 mb-1 ${
                    stage.status === 'done'
                      ? 'bg-brand-500'
                      : 'bg-[#2a2a2a]'
                  }`}
                  style={{ minHeight: '20px' }}
                />
              )}
            </div>
            {/* Content */}
            <div className={`pb-4 ${idx === stages.length - 1 ? 'pb-0' : ''}`}>
              <p
                className={`text-sm font-medium leading-6 ${
                  stage.status === 'done'
                    ? 'text-[#9a9ba8]'
                    : stage.status === 'active'
                    ? 'text-white'
                    : stage.status === 'error'
                    ? 'text-red-400'
                    : 'text-[#444]'
                }`}
              >
                {stage.label}
                {stage.status === 'active' && (
                  <span className="ml-2 text-xs text-brand-400 font-normal animate-pulse">
                    running...
                  </span>
                )}
              </p>
              {stage.message && stage.status === 'active' && (
                <p className="text-xs text-[#7e8088] mt-0.5">{stage.message}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {error && (
        <div className="mt-4 px-3 py-2 bg-red-900/30 border border-red-800/50 rounded text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
