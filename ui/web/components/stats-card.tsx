'use client';

import { cn, formatNumber, formatPercentage } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: number;
    label: string;
  };
  variant?: 'default' | 'accent' | 'success' | 'warning';
  className?: string;
}

export function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  variant = 'default',
  className,
}: StatsCardProps) {
  const variantStyles = {
    default: {
      bg: 'bg-[var(--bg-surface)]',
      border: 'border-[var(--border-subtle)]',
      icon: 'bg-[var(--bg-elevated)] text-[var(--text-secondary)]',
      value: 'text-[var(--text-primary)]',
    },
    accent: {
      bg: 'bg-gradient-to-br from-[var(--accent-primary)]/10 to-transparent',
      border: 'border-[var(--accent-primary)]/30',
      icon: 'bg-[var(--accent-primary)]/20 text-[var(--accent-primary)]',
      value: 'text-[var(--accent-primary)]',
    },
    success: {
      bg: 'bg-gradient-to-br from-[var(--success)]/10 to-transparent',
      border: 'border-[var(--success)]/30',
      icon: 'bg-[var(--success)]/20 text-[var(--success)]',
      value: 'text-[var(--success)]',
    },
    warning: {
      bg: 'bg-gradient-to-br from-[var(--warning)]/10 to-transparent',
      border: 'border-[var(--warning)]/30',
      icon: 'bg-[var(--warning)]/20 text-[var(--warning)]',
      value: 'text-[var(--warning)]',
    },
  };

  const styles = variantStyles[variant];

  return (
    <div
      className={cn(
        'relative overflow-hidden border p-5 transition-all hover:border-[var(--border-default)]',
        styles.bg,
        styles.border,
        className
      )}
    >
      {/* Corner accent */}
      <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-bl from-[var(--bg-hover)]/50 to-transparent" />

      <div className="flex items-start justify-between">
        <div className="space-y-3">
          <p className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)]">
            {title}
          </p>
          <p className={cn('font-mono text-3xl font-bold tracking-tight', styles.value)}>
            {formatNumber(value)}
          </p>
          {subtitle && (
            <p className="font-mono text-xs text-[var(--text-muted)]">{subtitle}</p>
          )}
          {trend && (
            <div className="flex items-center gap-1.5">
              <span className={cn(
                'font-mono text-xs',
                trend.value >= 0 ? 'text-[var(--success)]' : 'text-[var(--danger)]'
              )}>
                {trend.value >= 0 ? '+' : ''}{formatPercentage(trend.value)}
              </span>
              <span className="font-mono text-xs text-[var(--text-muted)]">
                {trend.label}
              </span>
            </div>
          )}
        </div>
        <div className={cn('flex h-10 w-10 items-center justify-center', styles.icon)}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

export function StatsCardSkeleton() {
  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5">
      <div className="flex items-start justify-between">
        <div className="space-y-3">
          <div className="skeleton h-3 w-20" />
          <div className="skeleton h-8 w-24" />
          <div className="skeleton h-3 w-16" />
        </div>
        <div className="skeleton h-10 w-10" />
      </div>
    </div>
  );
}
