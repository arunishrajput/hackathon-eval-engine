'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { submissionApi } from '@/lib/api';

const GITHUB_URL_RE = /^https?:\/\/(www\.)?github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+(\/.*)?$/;

type ValidationState = 'idle' | 'valid' | 'invalid';

export default function SubmitPage() {
  const { hackathonId } = useParams<{ hackathonId: string }>();
  const router = useRouter();
  const [repoUrl, setRepoUrl] = useState('');
  const [urlState, setUrlState] = useState<ValidationState>('idle');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const validateUrl = (url: string): ValidationState => {
    if (!url) return 'idle';
    return GITHUB_URL_RE.test(url.trim()) ? 'valid' : 'invalid';
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setRepoUrl(v);
    setUrlState(validateUrl(v));
    if (error) setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const state = validateUrl(repoUrl);
    setUrlState(state);
    if (state !== 'valid') {
      setError('Please enter a valid public GitHub repository URL');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const submission = await submissionApi.create(hackathonId, repoUrl.trim());
      router.push(`/participant/evaluation/${submission.id}`);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr?.response?.data?.detail ?? 'Submission failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const borderClass =
    urlState === 'valid'
      ? 'border-emerald-600 focus:ring-emerald-700'
      : urlState === 'invalid'
      ? 'border-red-700 focus:ring-red-700'
      : 'border-[#3a3b48] focus:ring-brand-600';

  return (
    <div className="max-w-xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Submit Your Project</h1>
        <p className="text-[#7e8088] text-sm mt-1">
          Provide your public GitHub repository URL to begin AI evaluation
        </p>
      </div>

      <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-6">
        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="bg-red-900/30 border border-red-800/50 text-red-400 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-[#dddfe4] mb-1.5">
              GitHub Repository URL <span className="text-red-400">*</span>
            </label>
            <div className="relative">
              <input
                type="url"
                required
                placeholder="https://github.com/username/repo"
                value={repoUrl}
                onChange={handleUrlChange}
                className={`w-full bg-[#13141a] border rounded-lg px-3 py-2.5 pr-10 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 transition ${borderClass}`}
              />
              {urlState !== 'idle' && (
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-base">
                  {urlState === 'valid' ? (
                    <span className="text-emerald-400">&#10003;</span>
                  ) : (
                    <span className="text-red-400">&#10007;</span>
                  )}
                </span>
              )}
            </div>
            <p className="mt-1.5 text-xs text-[#7e8088]">
              Must be a public GitHub repository (e.g.{' '}
              <span className="font-mono text-[#9a9ba8]">github.com/user/repo</span>)
            </p>
            {urlState === 'invalid' && (
              <p className="mt-1 text-xs text-red-400">
                Enter a valid GitHub URL like https://github.com/username/repo-name
              </p>
            )}
          </div>

          {/* Preview when valid */}
          {urlState === 'valid' && (
            <div className="flex items-center gap-2 text-xs text-[#9a9ba8] bg-[#13141a] border border-[#1a1a1a] rounded-lg px-3 py-2">
              <svg className="w-4 h-4 text-[#7e8088] flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.477 2 2 6.477 2 12c0 4.418 2.865 8.168 6.839 9.49.5.092.682-.217.682-.482 0-.237-.009-.868-.013-1.703-2.782.605-3.369-1.342-3.369-1.342-.454-1.155-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.031 1.531 1.031.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.112-4.555-4.951 0-1.093.39-1.988 1.03-2.688-.104-.253-.447-1.272.098-2.65 0 0 .84-.269 2.75 1.026A9.578 9.578 0 0112 6.836c.85.004 1.705.115 2.504.337 1.909-1.295 2.748-1.026 2.748-1.026.546 1.378.203 2.397.1 2.65.64.7 1.028 1.595 1.028 2.688 0 3.848-2.338 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.579.688.481C19.138 20.164 22 16.416 22 12c0-5.523-4.477-10-10-10z" />
              </svg>
              <span className="truncate">{repoUrl}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || urlState === 'invalid'}
            className="w-full py-2.5 px-4 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-semibold text-sm transition-colors"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Submitting...
              </span>
            ) : (
              'Submit Project'
            )}
          </button>
        </form>

        {/* Info box */}
        <div className="mt-6 pt-5 border-t border-[#1a1a1a]">
          <p className="text-xs font-semibold text-[#7e8088] uppercase tracking-wide mb-3">
            What happens next?
          </p>
          <ul className="space-y-2">
            {[
              'Your repository will be cloned securely',
              'AI agents analyze your code structure and quality',
              'Scores are aggregated across all evaluation criteria',
              'You get a detailed report with actionable feedback',
            ].map((step, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-[#7e8088]">
                <span className="flex-shrink-0 w-4 h-4 rounded-full bg-[#252630] border border-[#3a3b48] flex items-center justify-center text-[#5a5c66] font-bold text-[10px]">
                  {i + 1}
                </span>
                {step}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
