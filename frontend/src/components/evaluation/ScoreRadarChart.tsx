'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  ResponsiveContainer,
  Tooltip,
  ReferenceLine,
  LabelList,
} from 'recharts';
import type { AgentResult } from '@/lib/types';

interface Props {
  agentResults: AgentResult[];
}

const AGENT_LABELS: Record<string, string> = {
  repo_understanding: 'Structure',
  code_quality: 'Code Quality',
  innovation: 'Innovation',
  comparative: 'Comparative',
  documentation: 'Docs',
  testing: 'Testing',
  security: 'Security',
};

interface TooltipPayload {
  subject: string;
  score: number;
  rawScore: number | null;
  abstained: boolean;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: TooltipPayload }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const { subject, rawScore, abstained } = payload[0].payload;
  return (
    <div className="bg-[#252630] border border-[#3a3b48] rounded-lg px-3 py-2 shadow-lg">
      <p className="text-xs text-[#9a9ba8] mb-0.5">{subject}</p>
      {abstained ? (
        <p className="text-sm font-bold text-[#5a5c66]">Abstained</p>
      ) : (
        <p className="text-sm font-bold text-[#b1361e]">{Number(rawScore).toFixed(1)} / 10</p>
      )}
    </div>
  );
}

function makeScoreLabel(rows: Array<{ abstained: boolean }>) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return function ScoreLabel(props: any) {
    const { x, y, width, height, value, index } = props as {
      x: number; y: number; width: number; height: number; value: number; index: number;
    };
    if (rows[index]?.abstained) {
      return (
        <text x={x + width + 8} y={y + height / 2 + 4} fill="#ef4444" fontSize={10} fontFamily="Inter, sans-serif" fontWeight="500">
          Failed
        </text>
      );
    }
    return (
      <text x={x + width + 8} y={y + height / 2 + 4} fill="#9a9ba8" fontSize={11} fontFamily="ui-monospace, monospace">
        {Number(value).toFixed(1)}
      </text>
    );
  };
}

export function ScoreRadarChart({ agentResults }: Props) {
  if (agentResults.length === 0) {
    return (
      <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-6 flex items-center justify-center h-64">
        <p className="text-[#7e8088] text-sm">No agent scores available</p>
      </div>
    );
  }

  const data = agentResults.map((r) => ({
    subject: AGENT_LABELS[r.agent_id] ?? r.agent_id,
    score: r.abstained || r.score_raw == null ? 0 : r.score_raw,
    rawScore: r.score_raw,
    abstained: r.abstained,
  }));

  const chartHeight = Math.max(160, data.length * 52);

  return (
    <div className="bg-[#1c1d25] border border-[#2d2e3a] rounded-xl p-6">
      <h3 className="text-sm font-semibold text-[#dddfe4] tracking-wide uppercase mb-4">
        Score Breakdown
      </h3>
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 0, right: 44, bottom: 0, left: 4 }}
          barCategoryGap="32%"
        >
          <XAxis
            type="number"
            domain={[0, 10]}
            tickCount={6}
            tick={{ fill: '#4b4c57', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="subject"
            width={88}
            tick={{ fill: '#9ca3af', fontSize: 12, fontFamily: 'Inter, sans-serif' }}
            axisLine={false}
            tickLine={false}
          />
          <ReferenceLine x={5} stroke="#374151" strokeDasharray="4 4" strokeWidth={1} />
          <ReferenceLine x={7.5} stroke="#1e3a8a" strokeDasharray="3 3" strokeWidth={1} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <Bar dataKey="score" radius={[0, 3, 3, 0]} maxBarSize={20}>
            {data.map((entry, idx) => (
              <Cell
                key={idx}
                fill={entry.abstained ? '#23242f' : '#b1361e'}
                stroke={entry.abstained ? '#2d2e3a' : 'none'}
                fillOpacity={entry.abstained ? 1 : 0.9}
              />
            ))}
            <LabelList dataKey="score" content={makeScoreLabel(data)} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="flex items-center gap-4 mt-3 justify-center">
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-px block border-t-2 border-dashed border-[#374151]" />
          <span className="text-xs text-[#7e8088]">Baseline (5)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-px block border-t-2 border-dashed border-[#1e3a8a]" />
          <span className="text-xs text-[#7e8088]">Good (7.5)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm bg-[#b1361e]" />
          <span className="text-xs text-[#7e8088]">Score</span>
        </div>
      </div>
    </div>
  );
}
