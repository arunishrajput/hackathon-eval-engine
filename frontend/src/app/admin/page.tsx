'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { adminApi, hackathonApi } from '@/lib/api';
import type { Hackathon } from '@/lib/types';

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

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function AdminDashboardPage() {
  const [hackathons, setHackathons] = useState<Hackathon[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Try admin endpoint first, fall back to public list
    adminApi
      .listHackathons()
      .catch(() => hackathonApi.list())
      .then(setHackathons)
      .finally(() => setLoading(false));
  }, []);

  const byStatus = (status: string) =>
    hackathons.filter((h) => h.status === status).length;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
          <p className="text-[#7e8088] text-sm mt-0.5">
            Manage all hackathons and evaluation criteria
          </p>
        </div>
        <Link
          href="/admin/hackathons/new"
          className="px-4 py-2 bg-[#b1361e] hover:bg-blue-500 text-white rounded-lg font-medium text-sm transition-colors"
        >
          + New Hackathon
        </Link>
      </div>

      {/* Summary stats */}
      {!loading && hackathons.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Total', count: hackathons.length, color: 'text-[#dddfe4]' },
            { label: 'Active', count: byStatus('active'), color: 'text-emerald-400' },
            { label: 'Evaluating', count: byStatus('evaluating'), color: 'text-yellow-400' },
            { label: 'Finalized', count: byStatus('finalized'), color: 'text-[#b1361e]' },
          ].map(({ label, count, color }) => (
            <div
              key={label}
              className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl px-4 py-3"
            >
              <p className="text-xs text-[#7e8088] uppercase tracking-wide mb-1">{label}</p>
              <p className={`text-2xl font-bold font-mono ${color}`}>{count}</p>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <div className="text-center py-16">
          <span className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin inline-block" />
        </div>
      ) : hackathons.length === 0 ? (
        <div className="text-center py-16 bg-[#1c1d25] border border-[#2d2e3a] rounded-xl">
          <p className="text-[#9a9ba8] mb-2">No hackathons yet</p>
          <p className="text-[#5a5c66] text-sm">Create your first hackathon to get started</p>
          <Link
            href="/admin/hackathons/new"
            className="inline-block mt-4 px-5 py-2 bg-[#b1361e] hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Create Hackathon
          </Link>
        </div>
      ) : (
        <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl overflow-hidden">
          <div className="px-5 py-3.5 border-b border-[#2d2e3a]">
            <h2 className="text-sm font-semibold text-[#dddfe4]">All Hackathons</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-[#13141a] border-b border-[#2d2e3a]">
                  <th className="px-5 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                    Title
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                    Status
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide hidden md:table-cell">
                    Criteria
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-[#7e8088] uppercase tracking-wide hidden lg:table-cell">
                    Created
                  </th>
                  <th className="px-5 py-3 text-right text-xs font-semibold text-[#7e8088] uppercase tracking-wide">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {hackathons.map((h) => (
                  <tr key={h.id} className="hover:bg-[#1e1f27] transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="font-medium text-gray-200 text-sm">{h.title}</div>
                      {h.description && (
                        <div className="text-xs text-[#5a5c66] mt-0.5 line-clamp-1 max-w-[280px]">
                          {h.description}
                        </div>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          STATUS_STYLES[h.status] ?? STATUS_STYLES.draft
                        }`}
                      >
                        {STATUS_LABELS[h.status] ?? h.status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-sm text-[#7e8088] hidden md:table-cell">
                      {h.criteria?.length ?? 0} defined
                    </td>
                    <td className="px-5 py-3.5 text-sm text-[#7e8088] hidden lg:table-cell">
                      {formatDate(h.created_at)}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Link
                        href={`/admin/hackathons/${h.id}`}
                        className="text-xs text-[#b1361e] hover:text-[#e87060] border border-[#3a3b48] hover:border-[#b1361e] px-3 py-1.5 rounded-lg transition-colors font-medium"
                      >
                        Manage
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
