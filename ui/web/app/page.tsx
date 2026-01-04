'use client';

import { useQuery } from '@tanstack/react-query';
import {
  Users,
  CheckCircle2,
  Mail,
  Globe,
  Zap,
  TrendingUp,
} from 'lucide-react';
import { getStatsOverview, getScoreDistribution } from '@/lib/api';
import { StatsCard, StatsCardSkeleton } from '@/components/stats-card';
import { ProgressBar, ProgressBarSkeleton } from '@/components/progress-bar';
import { ScoreChart, ScoreChartSkeleton } from '@/components/score-chart';
import { formatNumber } from '@/lib/utils';

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats-overview'],
    queryFn: getStatsOverview,
  });

  const { data: scoreDistribution, isLoading: scoreLoading } = useQuery({
    queryKey: ['score-distribution'],
    queryFn: getScoreDistribution,
  });

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      {/* Header */}
      <div className="mb-8 animate-slide-up opacity-0">
        <div className="flex items-end gap-3">
          <h1 className="font-mono text-2xl font-bold tracking-tight text-[var(--text-primary)]">
            DASHBOARD
          </h1>
          <div className="h-1 w-12 bg-[var(--accent-primary)] mb-2" />
        </div>
        <p className="mt-2 font-mono text-sm text-[var(--text-tertiary)]">
          Real-time lead monitoring and analytics
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
        {statsLoading ? (
          <>
            <StatsCardSkeleton />
            <StatsCardSkeleton />
            <StatsCardSkeleton />
            <StatsCardSkeleton />
          </>
        ) : stats ? (
          <>
            <div className="animate-slide-up opacity-0 stagger-1">
              <StatsCard
                title="Total Leads"
                value={stats.total}
                subtitle="In database"
                icon={Users}
                variant="accent"
              />
            </div>
            <div className="animate-slide-up opacity-0 stagger-2">
              <StatsCard
                title="Qualified"
                value={stats.qualified}
                subtitle={`${((stats.qualified / stats.total) * 100).toFixed(1)}% of total`}
                icon={CheckCircle2}
                variant="success"
              />
            </div>
            <div className="animate-slide-up opacity-0 stagger-3">
              <StatsCard
                title="With Email"
                value={stats.with_email}
                subtitle="Contact ready"
                icon={Mail}
              />
            </div>
            <div className="animate-slide-up opacity-0 stagger-4">
              <StatsCard
                title="With Website"
                value={stats.with_website}
                subtitle="Web presence"
                icon={Globe}
              />
            </div>
          </>
        ) : null}
      </div>

      {/* Second Row */}
      <div className="grid gap-4 lg:grid-cols-3 mb-8">
        {/* Enrichment Progress */}
        <div className="lg:col-span-1 border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 animate-slide-up opacity-0 stagger-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)]">
              Enrichment Progress
            </h3>
            <Zap className="h-4 w-4 text-[var(--accent-primary)]" />
          </div>
          {statsLoading ? (
            <ProgressBarSkeleton />
          ) : stats ? (
            <>
              <ProgressBar
                value={stats.enrichment_percentage}
                label=""
                showPercentage
                size="lg"
              />
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <p className="font-mono text-2xl font-bold text-[var(--success)]">
                    {formatNumber(stats.enriched)}
                  </p>
                  <p className="font-mono text-xs text-[var(--text-muted)]">
                    Enriched
                  </p>
                </div>
                <div>
                  <p className="font-mono text-2xl font-bold text-[var(--text-tertiary)]">
                    {formatNumber(stats.not_enriched)}
                  </p>
                  <p className="font-mono text-xs text-[var(--text-muted)]">
                    Pending
                  </p>
                </div>
              </div>
            </>
          ) : null}
        </div>

        {/* Score Distribution Chart */}
        <div className="lg:col-span-2 animate-slide-up opacity-0 stagger-6">
          {scoreLoading ? (
            <ScoreChartSkeleton />
          ) : scoreDistribution ? (
            <ScoreChart data={scoreDistribution} />
          ) : null}
        </div>
      </div>

      {/* Quick Stats Bar */}
      {stats && (
        <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-[var(--accent-primary)]" />
              <span className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)]">
                Quick Stats
              </span>
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-[var(--text-muted)]">With Phone:</span>
                <span className="font-mono text-sm font-medium text-[var(--text-primary)]">
                  {formatNumber(stats.with_phone)}
                </span>
              </div>
              <div className="h-4 w-px bg-[var(--border-subtle)]" />
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-[var(--text-muted)]">Disqualified:</span>
                <span className="font-mono text-sm font-medium text-[var(--danger)]">
                  {formatNumber(stats.disqualified)}
                </span>
              </div>
              <div className="h-4 w-px bg-[var(--border-subtle)]" />
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-[var(--text-muted)]">Emailable Leads:</span>
                <span className="font-mono text-sm font-medium text-[var(--success)]">
                  {formatNumber(stats.with_email)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
