'use client';

import { useParams } from 'next/navigation';
import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { hackathonApi, adminApi } from '@/lib/api';
import type { Hackathon, Criterion } from '@/lib/types';

const AGENT_OPTIONS = [
  { value: 'repo_understanding', label: 'Repository Understanding' },
  { value: 'code_quality', label: 'Code Quality' },
  { value: 'innovation', label: 'Innovation & Creativity' },
  { value: 'comparative', label: 'Comparative Analysis' },
  { value: 'documentation', label: 'Documentation' },
  { value: 'testing', label: 'Testing Coverage' },
  { value: 'security', label: 'Security Analysis' },
];

interface EditableCriterion extends Criterion {
  _dirty?: boolean;
}

export default function CriteriaPage() {
  const { id } = useParams<{ id: string }>();
  const [hackathon, setHackathon] = useState<Hackathon | null>(null);
  const [criteria, setCriteria] = useState<EditableCriterion[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!id) return;
    const h = await hackathonApi.get(id);
    setHackathon(h);
    setCriteria(
      (h.criteria ?? [])
        .slice()
        .sort((a, b) => a.display_order - b.display_order)
    );
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const totalWeight = criteria.reduce((s, c) => s + (Number(c.weight) || 0), 0);
  const weightOk = Math.abs(totalWeight - 1.0) < 0.001;
  const weightPercent = Math.min(100, Math.round(totalWeight * 100));

  const update = (criterionId: string, field: keyof Criterion, value: string | number) => {
    setCriteria((prev) =>
      prev.map((c) =>
        c.id === criterionId ? { ...c, [field]: value, _dirty: true } : c
      )
    );
    setSaved(false);
  };

  const addCriterion = () => {
    const newC: EditableCriterion = {
      id: `new-${Date.now()}`,
      name: '',
      description: '',
      weight: 0.1,
      agent_id: 'code_quality',
      display_order: criteria.length,
      _dirty: true,
    };
    setCriteria((prev) => [...prev, newC]);
    setSaved(false);
  };

  const removeCriterion = (criterionId: string) => {
    setCriteria((prev) => prev.filter((c) => c.id !== criterionId));
    setSaved(false);
  };

  const distributeWeights = () => {
    const equal = parseFloat((1 / criteria.length).toFixed(4));
    setCriteria((prev) =>
      prev.map((c, i) => ({
        ...c,
        weight:
          i === prev.length - 1
            ? parseFloat((1 - equal * (prev.length - 1)).toFixed(4))
            : equal,
        _dirty: true,
      }))
    );
    setSaved(false);
  };

  const handleSave = async () => {
    if (!id) return;
    if (!weightOk) {
      setError(`Weights must sum to 1.0 (currently ${totalWeight.toFixed(3)})`);
      return;
    }
    if (criteria.some((c) => !c.name.trim())) {
      setError('All criteria must have names');
      return;
    }
    setError('');
    setSaving(true);
    try {
      await adminApi.updateCriteria(
        id,
        criteria.map((c, idx) => ({
          id: c.id.startsWith('new-') ? undefined : c.id,
          name: c.name,
          description: c.description || undefined,
          weight: Number(c.weight),
          agent_id: c.agent_id || undefined,
          display_order: idx,
        }))
      );
      setSaved(true);
      await load();
    } catch {
      setError('Failed to save criteria');
    } finally {
      setSaving(false);
    }
  };

  if (!hackathon) {
    return (
      <div className="flex items-center justify-center py-16">
        <span className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href={`/admin/hackathons/${id}`}
              className="text-xs text-[#5a5c66] hover:text-[#9a9ba8] transition-colors"
            >
              Hackathon
            </Link>
            <span className="text-gray-700">/</span>
            <span className="text-xs text-[#7e8088]">Criteria</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Evaluation Criteria</h1>
          <p className="text-[#7e8088] text-sm mt-0.5">{hackathon.title}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={distributeWeights}
            className="text-xs text-[#b1361e] hover:text-[#e87060] border border-[#3a3b48] hover:border-[#b1361e] px-2.5 py-1.5 rounded-lg transition-colors"
          >
            Distribute equally
          </button>
          <button
            onClick={handleSave}
            disabled={saving || (weightOk && !criteria.some((c) => c._dirty))}
            className="px-4 py-2 bg-[#b1361e] hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {saving ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Saving...
              </>
            ) : saved ? (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                Saved
              </>
            ) : (
              'Save Changes'
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 bg-red-900/30 border border-red-800/50 text-red-400 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Weight indicator */}
      <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-[#7e8088]">Total weight</span>
          <span
            className={`text-xs font-mono font-bold ${
              weightOk ? 'text-emerald-400' : 'text-yellow-400'
            }`}
          >
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
        {!weightOk && (
          <p className="text-xs text-yellow-500 mt-2">
            Weights must sum to exactly 1.0 before saving.
          </p>
        )}
      </div>

      {/* Criteria list */}
      <div className="space-y-3 mb-4">
        {criteria.map((c, idx) => (
          <div
            key={c.id}
            className={`bg-[#1c1d25] border rounded-xl p-5 transition-colors ${
              c._dirty ? 'border-[rgba(177,54,30,0.3)]' : 'border-[#2d2e3a]'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-[#5a5c66] font-mono">
                Criterion #{idx + 1}
                {c._dirty && (
                  <span className="ml-2 text-blue-500">• unsaved</span>
                )}
              </span>
              {criteria.length > 1 && (
                <button
                  onClick={() => removeCriterion(c.id)}
                  className="text-xs text-red-500 hover:text-red-400 transition-colors"
                >
                  Remove
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
              <div>
                <label className="block text-xs font-medium text-[#9a9ba8] mb-1">
                  Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={c.name}
                  onChange={(e) => update(c.id, 'name', e.target.value)}
                  placeholder="e.g. Code Quality"
                  className="w-full bg-[#13141a] border border-[#3a3b48] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-700 transition"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#9a9ba8] mb-1">
                  Weight (0–1)
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min={0}
                    max={1}
                    step={0.01}
                    value={c.weight}
                    onChange={(e) =>
                      update(c.id, 'weight', parseFloat(e.target.value) || 0)
                    }
                    className="w-full bg-[#13141a] border border-[#3a3b48] rounded-lg px-3 py-2 text-sm text-gray-200 font-mono focus:outline-none focus:border-blue-700 transition"
                  />
                  <span className="text-xs text-[#7e8088] whitespace-nowrap font-mono">
                    {(c.weight * 100).toFixed(0)}%
                  </span>
                </div>
                {/* Mini weight bar */}
                <div className="w-full h-1 bg-[#252630] rounded-full mt-1.5 overflow-hidden">
                  <div
                    className="h-1 bg-blue-600 rounded-full transition-all"
                    style={{ width: `${Math.min(100, c.weight * 100)}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="mb-3">
              <label className="block text-xs font-medium text-[#9a9ba8] mb-1">
                Evaluation Agent
              </label>
              <select
                value={c.agent_id ?? ''}
                onChange={(e) => update(c.id, 'agent_id', e.target.value)}
                className="w-full bg-[#13141a] border border-[#3a3b48] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-700 transition"
              >
                <option value="">— None —</option>
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
                value={c.description ?? ''}
                onChange={(e) => update(c.id, 'description', e.target.value)}
                placeholder="What should this criterion evaluate?"
                className="w-full bg-[#13141a] border border-[#3a3b48] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-700 transition"
              />
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={addCriterion}
        className="w-full py-2.5 border border-dashed border-[#3a3b48] hover:border-[#b1361e] text-[#7e8088] hover:text-[#b1361e] rounded-xl text-sm transition-colors"
      >
        + Add Criterion
      </button>
    </div>
  );
}
