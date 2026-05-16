'use client';

import { useEffect, useState } from 'react';
import { hackathonApi, submissionApi } from '@/lib/api';
import { HackathonCard } from '@/components/hackathon/HackathonCard';
import type { Hackathon, Submission } from '@/lib/types';

export default function ParticipantHackathonsPage() {
  const [hackathons, setHackathons] = useState<Hackathon[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([hackathonApi.list(), submissionApi.list()]).then(
      ([hackResult, subResult]) => {
        if (hackResult.status === 'fulfilled') setHackathons(hackResult.value);
        if (subResult.status === 'fulfilled') setSubmissions(subResult.value);
        setLoading(false);
      }
    );
  }, []);

  // Map hackathon_id -> submission_id for joined hackathons
  const joinedMap = new Map<string, string>();
  for (const s of submissions) {
    if (!joinedMap.has(s.hackathon_id)) {
      joinedMap.set(s.hackathon_id, s.id);
    }
  }

  // Separate active from others
  const active = hackathons.filter((h) => h.status === 'active');
  const others = hackathons.filter((h) => h.status !== 'active');

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Available Hackathons</h1>
        <p className="text-[#7e8088] text-sm mt-1">
          Browse and submit your project to active hackathons
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <span className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        </div>
      ) : hackathons.length === 0 ? (
        <div className="text-center py-16 bg-[#1c1d25] border border-[#2d2e3a] rounded-xl">
          <p className="text-[#9a9ba8]">No hackathons available at the moment</p>
          <p className="text-[#5a5c66] text-sm mt-1">Check back soon for upcoming events</p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Active */}
          {active.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-4">
                <h2 className="text-sm font-semibold text-[#9a9ba8] uppercase tracking-wide">
                  Open for Submissions
                </h2>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {active.map((h) => (
                  <HackathonCard
                    key={h.id}
                    hackathon={h}
                    role="participant"
                    joined={joinedMap.has(h.id)}
                    submissionId={joinedMap.get(h.id)}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Others */}
          {others.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-[#9a9ba8] uppercase tracking-wide mb-4">
                Other Hackathons
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {others.map((h) => (
                  <HackathonCard
                    key={h.id}
                    hackathon={h}
                    role="participant"
                    joined={joinedMap.has(h.id)}
                    submissionId={joinedMap.get(h.id)}
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
