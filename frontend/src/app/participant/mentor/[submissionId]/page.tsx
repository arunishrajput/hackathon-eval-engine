'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { evaluationApi, submissionApi } from '@/lib/api';
import { ChatInterface } from '@/components/mentor/ChatInterface';
import type { Evaluation, Submission } from '@/lib/types';

function GradeColor(grade: string): string {
  if (grade === 'A+' || grade === 'A') return 'text-emerald-400';
  if (grade === 'A-' || grade === 'B+') return 'text-[#b1361e]';
  if (grade === 'B' || grade === 'B-') return 'text-[#b1361e]';
  if (grade === 'C+' || grade === 'C') return 'text-yellow-400';
  return 'text-red-400';
}

const STARTER_QUESTIONS = [
  'Why did I score low on Code Quality?',
  'How can I improve my project architecture?',
  'What are the most critical issues in my code?',
  'How can I add better test coverage?',
];

export default function MentorPage() {
  const { submissionId } = useParams<{ submissionId: string }>();
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!submissionId) return;
    Promise.allSettled([
      evaluationApi.get(submissionId),
      submissionApi.get(submissionId),
    ]).then(([evalResult, subResult]) => {
      if (evalResult.status === 'fulfilled') setEvaluation(evalResult.value);
      if (subResult.status === 'fulfilled') setSubmission(subResult.value);
      setLoading(false);
    });
  }, [submissionId]);

  const isComplete = evaluation?.status === 'completed';

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <span className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (!isComplete) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center">
        <div className="w-14 h-14 rounded-full bg-[#252630] border border-[#3a3b48] flex items-center justify-center mx-auto mb-5">
          <svg
            className="w-7 h-7 text-[#5a5c66]"
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
        </div>
        <h2 className="text-lg font-semibold text-white mb-2">Mentor Not Available Yet</h2>
        <p className="text-[#7e8088] text-sm leading-relaxed max-w-sm mx-auto">
          Evaluation must be completed before using the AI Mentor. Check back once your
          submission has been fully evaluated.
        </p>
        <Link
          href={`/participant/evaluation/${submissionId}`}
          className="inline-block mt-5 px-5 py-2.5 bg-[#b1361e] hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          View Evaluation Status
        </Link>
      </div>
    );
  }

  const report = evaluation?.report;

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Page title */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Mentor</h1>
          <p className="text-[#7e8088] text-sm mt-0.5">
            Context-aware guidance powered by your evaluation results
          </p>
        </div>
        <Link
          href={`/participant/evaluation/${submissionId}`}
          className="text-xs text-[#b1361e] hover:text-[#e87060] border border-[#3a3b48] hover:border-[#b1361e] px-3 py-1.5 rounded-lg transition-colors"
        >
          View Full Report
        </Link>
      </div>

      <div className="flex flex-col lg:flex-row gap-4 flex-1 min-h-0">
        {/* Left panel: evaluation summary */}
        <div className="lg:w-72 flex-shrink-0 space-y-4 overflow-y-auto">
          {/* Score card */}
          <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-5">
            <p className="text-xs font-semibold text-[#7e8088] uppercase tracking-wide mb-3">
              Your Score
            </p>
            <div className="flex items-end gap-2 mb-3">
              <span className="text-4xl font-bold text-[#b1361e] font-mono leading-none">
                {evaluation.final_score?.toFixed(1) ?? '—'}
              </span>
              <span className="text-[#5a5c66] text-sm mb-1">/ 10</span>
            </div>
            {report?.grade && (
              <span className={`text-2xl font-bold ${GradeColor(report.grade)}`}>
                Grade: {report.grade}
              </span>
            )}
            {submission && (
              <div className="mt-3 pt-3 border-t border-[#1a1a1a]">
                <a
                  href={submission.repo_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-[#5a5c66] hover:text-[#b1361e] transition-colors font-mono truncate block"
                >
                  {submission.repo_url.replace('https://github.com/', '')}
                </a>
              </div>
            )}
          </div>

          {/* Top strengths */}
          {report?.top_strengths && report.top_strengths.length > 0 && (
            <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-5">
              <p className="text-xs font-semibold text-[#7e8088] uppercase tracking-wide mb-3">
                Top Strengths
              </p>
              <ul className="space-y-2">
                {report.top_strengths.slice(0, 3).map((s, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5" />
                    <span className="text-xs text-[#9a9ba8] leading-relaxed">{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Top weaknesses */}
          {report?.top_weaknesses && report.top_weaknesses.length > 0 && (
            <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-5">
              <p className="text-xs font-semibold text-[#7e8088] uppercase tracking-wide mb-3">
                Areas to Improve
              </p>
              <ul className="space-y-2">
                {report.top_weaknesses.slice(0, 3).map((w, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5" />
                    <span className="text-xs text-[#9a9ba8] leading-relaxed">{w}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Starter questions hint */}
          <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-5">
            <p className="text-xs font-semibold text-[#7e8088] uppercase tracking-wide mb-3">
              Suggested Questions
            </p>
            <ul className="space-y-2">
              {STARTER_QUESTIONS.map((q, i) => (
                <li
                  key={i}
                  className="text-xs text-[#7e8088] flex items-start gap-1.5"
                >
                  <span className="text-[#b1361e] flex-shrink-0 mt-0.5">&#8250;</span>
                  {q}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right panel: chat */}
        <div className="flex-1 min-h-0 flex flex-col">
          <ChatInterface submissionId={submissionId} />
        </div>
      </div>
    </div>
  );
}
