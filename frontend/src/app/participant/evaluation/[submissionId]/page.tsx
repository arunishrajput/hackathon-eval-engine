'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { evaluationApi, submissionApi } from '@/lib/api';
import { ProgressStream } from '@/components/evaluation/ProgressStream';
import { ReportViewer } from '@/components/evaluation/ReportViewer';
import { ScoreRadarChart } from '@/components/evaluation/ScoreRadarChart';
import type { Evaluation, Submission } from '@/lib/types';

function GradeColor(grade: string): string {
  if (grade === 'A+' || grade === 'A') return 'text-emerald-400';
  if (grade === 'A-' || grade === 'B+') return 'text-[#b1361e]';
  if (grade === 'B' || grade === 'B-') return 'text-[#b1361e]';
  if (grade === 'C+' || grade === 'C') return 'text-yellow-400';
  return 'text-red-400';
}

export default function EvaluationPage() {
  const { submissionId } = useParams<{ submissionId: string }>();
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!submissionId) return;
    Promise.allSettled([
      evaluationApi.get(submissionId),
      submissionApi.get(submissionId),
    ])
      .then(([evalResult, subResult]) => {
        if (evalResult.status === 'fulfilled') setEvaluation(evalResult.value);
        if (subResult.status === 'fulfilled') setSubmission(subResult.value);
      })
      .finally(() => setLoading(false));
  }, [submissionId]);

  const handleStreamComplete = (evalData: Evaluation) => {
    setEvaluation(evalData);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <span className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  const isComplete = evaluation?.status === 'completed';
  const isFailed = evaluation?.status === 'failed';

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Evaluation Results</h1>
          {submission && (
            <div className="flex items-center gap-2 mt-2">
              <a
                href={submission.repo_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-[#b1361e] hover:text-[#e87060] transition-colors font-mono flex items-center gap-1.5"
              >
                <svg
                  className="w-3.5 h-3.5 flex-shrink-0"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 2C6.477 2 2 6.477 2 12c0 4.418 2.865 8.168 6.839 9.49.5.092.682-.217.682-.482 0-.237-.009-.868-.013-1.703-2.782.605-3.369-1.342-3.369-1.342-.454-1.155-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.031 1.531 1.031.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.112-4.555-4.951 0-1.093.39-1.988 1.03-2.688-.104-.253-.447-1.272.098-2.65 0 0 .84-.269 2.75 1.026A9.578 9.578 0 0112 6.836c.85.004 1.705.115 2.504.337 1.909-1.295 2.748-1.026 2.748-1.026.546 1.378.203 2.397.1 2.65.64.7 1.028 1.595 1.028 2.688 0 3.848-2.338 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.579.688.481C19.138 20.164 22 16.416 22 12c0-5.523-4.477-10-10-10z" />
                </svg>
                {submission.repo_url.replace('https://github.com/', '')}
              </a>
              <span className="text-gray-700">·</span>
              <span className="text-xs text-[#5a5c66]">
                Submitted{' '}
                {new Date(submission.submitted_at).toLocaleDateString(undefined, {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </span>
            </div>
          )}
          {!submission && (
            <p className="text-[#7e8088] text-sm mt-1">
              ID:{' '}
              <span className="font-mono text-[#9a9ba8]">{submissionId}</span>
            </p>
          )}
        </div>

        {isComplete && (
          <Link
            href={`/participant/mentor/${submissionId}`}
            className="flex-shrink-0 flex items-center gap-1.5 px-4 py-2 bg-[#1c1d25] border border-[#3a3b48] hover:border-[#b1361e] text-[#dddfe4] hover:text-white rounded-lg text-sm font-medium transition-colors"
          >
            <svg
              className="w-4 h-4 text-[#b1361e]"
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
            Chat with Mentor
          </Link>
        )}
      </div>

      {/* Progress stream (when still running) */}
      {!isComplete && !isFailed && (
        <ProgressStream submissionId={submissionId} onComplete={handleStreamComplete} />
      )}

      {/* Error state */}
      {isFailed && (
        <div className="bg-red-900/30 border border-red-800/50 text-red-400 px-4 py-3 rounded-xl text-sm">
          Evaluation failed.{' '}
          {evaluation?.report
            ? 'Partial results may be shown below.'
            : 'Please try re-submitting your project.'}
        </div>
      )}

      {isComplete && evaluation && (
        <>
          {/* Score hero + radar */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Score panel (sticky on larger screens via layout) */}
            <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-6 flex flex-col items-center justify-center text-center">
              <div className="text-xs font-semibold text-[#7e8088] uppercase tracking-wide mb-3">
                Final Score
              </div>
              <div className="text-6xl font-bold text-[#b1361e] font-mono leading-none">
                {evaluation.final_score?.toFixed(1) ?? '—'}
              </div>
              <div className="text-[#5a5c66] text-sm mt-1">out of 10</div>

              {evaluation.report?.grade && (
                <div
                  className={`text-3xl font-bold mt-4 ${GradeColor(evaluation.report.grade)}`}
                >
                  Grade: {evaluation.report.grade}
                </div>
              )}

              {/* Metadata pills */}
              {evaluation.report?.metadata && (
                <div className="flex flex-wrap justify-center gap-2 mt-4">
                  {evaluation.report.metadata.primary_language && (
                    <span className="px-2 py-0.5 bg-[#252630] border border-[#3a3b48] rounded text-xs text-[#7e8088] font-mono">
                      {evaluation.report.metadata.primary_language}
                    </span>
                  )}
                  {evaluation.report.metadata.has_tests && (
                    <span className="px-2 py-0.5 bg-emerald-900/20 border border-emerald-800/40 rounded text-xs text-emerald-400">
                      Tests
                    </span>
                  )}
                  {evaluation.report.metadata.has_docker && (
                    <span className="px-2 py-0.5 bg-[rgba(177,54,30,0.10)] border border-[rgba(177,54,30,0.3)] rounded text-xs text-[#b1361e]">
                      Docker
                    </span>
                  )}
                  {evaluation.report.metadata.has_ci && (
                    <span className="px-2 py-0.5 bg-purple-900/20 border border-purple-800/40 rounded text-xs text-purple-400">
                      CI
                    </span>
                  )}
                </div>
              )}

              {evaluation.completed_at && (
                <div className="text-xs text-[#5a5c66] mt-4">
                  Completed{' '}
                  {new Date(evaluation.completed_at).toLocaleString(undefined, {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  })}
                </div>
              )}

              {/* Mentor CTA */}
              <Link
                href={`/participant/mentor/${submissionId}`}
                className="mt-5 w-full flex items-center justify-center gap-2 py-2 px-4 bg-[rgba(177,54,30,0.10)] hover:bg-[rgba(177,54,30,0.12)] border border-[rgba(177,54,30,0.3)] hover:border-blue-700 text-[#b1361e] rounded-lg text-sm font-medium transition-colors"
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
                    d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"
                  />
                </svg>
                Ask the AI Mentor
              </Link>
            </div>

            <ScoreRadarChart agentResults={evaluation.agent_results ?? []} />
          </div>

          <ReportViewer evaluation={evaluation} />
        </>
      )}
    </div>
  );
}
