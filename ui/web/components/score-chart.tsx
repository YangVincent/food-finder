'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { ScoreDistribution } from '@/lib/types';
import { formatNumber } from '@/lib/utils';

interface ScoreChartProps {
  data: ScoreDistribution[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[var(--bg-elevated)] border border-[var(--border-default)] px-3 py-2">
        <p className="font-mono text-xs text-[var(--text-secondary)]">
          Score Range: {label}
        </p>
        <p className="font-mono text-sm font-bold text-[var(--accent-primary)]">
          {formatNumber(payload[0].value)} leads
        </p>
      </div>
    );
  }
  return null;
};

export function ScoreChart({ data }: ScoreChartProps) {
  const getBarColor = (range: string) => {
    switch (range) {
      case '0-20':
        return 'var(--border-strong)';
      case '21-40':
        return '#eab308';
      case '41-60':
        return '#22c55e';
      case '61-80':
        return 'var(--accent-primary)';
      default:
        return 'var(--text-tertiary)';
    }
  };

  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5">
      <div className="mb-4">
        <h3 className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)]">
          Score Distribution
        </h3>
      </div>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <XAxis
              dataKey="range"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'var(--text-tertiary)', fontSize: 11, fontFamily: 'JetBrains Mono' }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'var(--text-muted)', fontSize: 10, fontFamily: 'JetBrains Mono' }}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--bg-hover)' }} />
            <Bar dataKey="count" radius={[2, 2, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.range)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4">
        {[
          { range: '0-20', label: 'Low', color: 'var(--border-strong)' },
          { range: '21-40', label: 'Fair', color: '#eab308' },
          { range: '41-60', label: 'Good', color: '#22c55e' },
          { range: '61-80', label: 'Excellent', color: 'var(--accent-primary)' },
        ].map((item) => (
          <div key={item.range} className="flex items-center gap-2">
            <div
              className="h-2 w-4"
              style={{ backgroundColor: item.color }}
            />
            <span className="font-mono text-xs text-[var(--text-muted)]">
              {item.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ScoreChartSkeleton() {
  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5">
      <div className="skeleton h-3 w-32 mb-4" />
      <div className="skeleton h-48 w-full" />
    </div>
  );
}
