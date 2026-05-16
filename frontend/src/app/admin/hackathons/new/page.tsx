'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { hackathonApi } from '@/lib/api';

const AGENT_OPTIONS = [
  { value: 'repo_understanding', label: 'Repository Understanding' },
  { value: 'code_quality', label: 'Code Quality' },
  { value: 'innovation', label: 'Innovation & Creativity' },
  { value: 'comparative', label: 'Comparative Analysis' },
  { value: 'documentation', label: 'Documentation' },
  { value: 'testing', label: 'Testing Coverage' },
  { value: 'security', label: 'Security Analysis' },
];

interface CriterionRow {
  id: string;
  name: string;
  description: string;
  weight: number;
  agent_id: string;
}

function newCriterion(): CriterionRow {
  return {
    id: `temp-${Date.now()}-${Math.random()}`,
    name: '',
    description: '',
    weight: 0.25,
    agent_id: 'code_quality',
  };
}

export default function NewHackathonPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    title: '',
    description: '',
    start_date: '',
    end_date: '',
    max_submissions: 100,
  });
  const [criteria, setCriteria] = useState<CriterionRow[]>([newCriterion()]);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const totalWeight = criteria.reduce((sum, c) => sum + (Number(c.weight) || 0), 0);
  const weightPercent = Math.min(100, Math.round(totalWeight * 100));
  const weightOk = Math.abs(totalWeight - 1.0) < 0.001;

  const addCriterion = () => setCriteria((prev) => [...prev, newCriterion()]);

  const removeCriterion = (id: string) =>
    setCriteria((prev) => prev.filter((c) => c.id !== id));

  const updateCriterion = (id: string, field: keyof CriterionRow, value: string | number) =>
    setCriteria((prev) =>
      prev.map((c) => (c.id === id ? { ...c, [field]: value } : c))
    );

  const distributeWeights = () => {
    const equal = parseFloat((1 / criteria.length).toFixed(4));
    const adjusted = criteria.map((c, i) => ({
      ...c,
      weight: i === criteria.length - 1
        ? parseFloat((1 - equal * (criteria.length - 1)).toFixed(4))
        : equal,
    }));
    setCriteria(adjusted);
  };

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!form.title.trim()) errs.title = 'Title is required';
    if (criteria.some((c) => !c.name.trim())) errs.criteria = 'All criteria must have names';
    if (!weightOk) errs.weight = `Weights must sum to 1.0 (currently ${totalWeight.toFixed(3)})`;
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setError('');
    setLoading(true);
    try {
      const payload = {
        ...form,
        start_date: form.start_date || undefined,
        end_date: form.end_date || undefined,
        criteria: criteria.map((c, idx) => ({
          name: c.name,
          description: c.description || undefined,
          weight: Number(c.weight),
          agent_id: c.agent_id || undefined,
          display_order: idx,
        })),
      };
      const h = await hackathonApi.create(payload);
      router.push(`/admin/hackathons/${h.id}`);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr?.response?.data?.detail ?? 'Failed to create hackathon');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Create New Hackathon</h1>
        <p className="text-[#7e8088] text-sm mt-1">Configure your hackathon and evaluation criteria</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="bg-red-900/30 border border-red-800/50 text-red-400 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Basic info */}
        <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-6 space-y-5">
          <h2 className="text-sm font-semibold text-[#9a9ba8] uppercase tracking-wide">
            Basic Information
          </h2>

          <div>
            <label className="block text-sm font-medium text-[#dddfe4] mb-1.5">
              Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="e.g. Spring AI Hackathon 2025"
              className={`w-full bg-[#13141a] border rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-600 transition ${
                fieldErrors.title ? 'border-red-700' : 'border-[#3a3b48]'
              }`}
            />
            {fieldErrors.title && <p className="mt-1 text-xs text-red-400">{fieldErrors.title}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-[#dddfe4] mb-1.5">Description</label>
            <textarea
              rows={3}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Describe the hackathon theme, goals, and rules..."
              className="w-full bg-[#13141a] border border-[#3a3b48] rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-600 transition resize-none"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[#dddfe4] mb-1.5">Start Date</label>
              <input
                type="datetime-local"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                className="w-full bg-[#13141a] border border-[#3a3b48] rounded-lg px-3 py-2.5 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-600 transition"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[#dddfe4] mb-1.5">End Date</label>
              <input
                type="datetime-local"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                className="w-full bg-[#13141a] border border-[#3a3b48] rounded-lg px-3 py-2.5 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-600 transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#dddfe4] mb-1.5">Max Submissions</label>
            <input
              type="number"
              min={1}
              max={10000}
              value={form.max_submissions}
              onChange={(e) => setForm({ ...form, max_submissions: parseInt(e.target.value) || 1 })}
              className="w-full bg-[#13141a] border border-[#3a3b48] rounded-lg px-3 py-2.5 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-600 transition"
            />
          </div>
        </div>

        {/* Criteria builder */}
        <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[#9a9ba8] uppercase tracking-wide">
              Evaluation Criteria
            </h2>
            <button
              type="button"
              onClick={distributeWeights}
              className="text-xs text-brand-400 hover:text-brand-300 border border-[#3a3b48] hover:border-brand-800 px-2.5 py-1 rounded transition"
            >
              Distribute equally
            </button>
          </div>

          {/* Weight progress bar */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-[#7e8088]">Total weight</span>
              <span className={`text-xs font-mono font-bold ${weightOk ? 'text-emerald-400' : 'text-yellow-400'}`}>
                {totalWeight.toFixed(3)} / 1.000
              </span>
            </div>
            <div className="w-full bg-[#252630] rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  weightOk
                    ? 'bg-emerald-500'
                    : totalWeight > 1
                    ? 'bg-red-500'
                    : 'bg-yellow-500'
                }`}
                style={{ width: `${weightPercent}%` }}
              />
            </div>
            {fieldErrors.weight && (
              <p className="mt-1 text-xs text-red-400">{fieldErrors.weight}</p>
            )}
          </div>

          {/* Criteria rows */}
          <div className="space-y-3">
            {criteria.map((c, idx) => (
              <div
                key={c.id}
                className="bg-[#13141a] border border-[#1a1a1a] rounded-lg p-4 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#5a5c66] font-mono">Criterion #{idx + 1}</span>
                  {criteria.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeCriterion(c.id)}
                      className="text-xs text-red-500 hover:text-red-400 transition"
                    >
                      Remove
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-[#9a9ba8] mb-1">Name *</label>
                    <input
                      type="text"
                      required
                      value={c.name}
                      onChange={(e) => updateCriterion(c.id, 'name', e.target.value)}
                      placeholder="e.g. Code Quality"
                      className="w-full bg-[#1c1d25] border border-[#3a3b48] rounded-md px-2.5 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-brand-700 transition"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-[#9a9ba8] mb-1">
                      Weight (0–1)
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={1}
                      step={0.01}
                      value={c.weight}
                      onChange={(e) =>
                        updateCriterion(c.id, 'weight', parseFloat(e.target.value) || 0)
                      }
                      className="w-full bg-[#1c1d25] border border-[#3a3b48] rounded-md px-2.5 py-2 text-sm text-gray-200 font-mono focus:outline-none focus:border-brand-700 transition"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#9a9ba8] mb-1">
                    Evaluation Agent
                  </label>
                  <select
                    value={c.agent_id}
                    onChange={(e) => updateCriterion(c.id, 'agent_id', e.target.value)}
                    className="w-full bg-[#1c1d25] border border-[#3a3b48] rounded-md px-2.5 py-2 text-sm text-gray-200 focus:outline-none focus:border-brand-700 transition"
                  >
                    {AGENT_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#9a9ba8] mb-1">
                    Description (optional)
                  </label>
                  <input
                    type="text"
                    value={c.description}
                    onChange={(e) => updateCriterion(c.id, 'description', e.target.value)}
                    placeholder="What should this criterion evaluate?"
                    className="w-full bg-[#1c1d25] border border-[#3a3b48] rounded-md px-2.5 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-brand-700 transition"
                  />
                </div>
              </div>
            ))}
          </div>

          {fieldErrors.criteria && (
            <p className="text-xs text-red-400">{fieldErrors.criteria}</p>
          )}

          <button
            type="button"
            onClick={addCriterion}
            className="w-full py-2 border border-dashed border-[#3a3b48] hover:border-brand-800 text-[#7e8088] hover:text-brand-400 rounded-lg text-sm transition-colors"
          >
            + Add Criterion
          </button>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 py-2.5 px-4 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-semibold text-sm transition-colors"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Creating...
              </span>
            ) : (
              'Create Hackathon'
            )}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="px-5 py-2.5 border border-[#3a3b48] hover:border-[#4a4b58] text-[#9a9ba8] hover:text-gray-200 rounded-lg text-sm font-medium transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
