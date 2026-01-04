'use client';

import { cn, formatPercentage } from '@/lib/utils';

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  variant?: 'default' | 'accent' | 'success';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function ProgressBar({
  value,
  max = 100,
  label,
  showPercentage = true,
  variant = 'accent',
  size = 'md',
  className,
}: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100);

  const variantStyles = {
    default: 'bg-[var(--text-tertiary)]',
    accent: 'bg-gradient-to-r from-[var(--accent-primary)] to-[var(--accent-secondary)]',
    success: 'bg-[var(--success)]',
  };

  const sizeStyles = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div className={cn('space-y-2', className)}>
      {(label || showPercentage) && (
        <div className="flex items-center justify-between">
          {label && (
            <span className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)]">
              {label}
            </span>
          )}
          {showPercentage && (
            <span className="font-mono text-sm font-medium text-[var(--text-primary)]">
              {formatPercentage(percentage)}
            </span>
          )}
        </div>
      )}
      <div className={cn('w-full bg-[var(--bg-elevated)] overflow-hidden', sizeStyles[size])}>
        <div
          className={cn(
            'h-full transition-all duration-500 ease-out',
            variantStyles[variant]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

export function ProgressBarSkeleton() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="skeleton h-3 w-24" />
        <div className="skeleton h-4 w-12" />
      </div>
      <div className="skeleton h-2 w-full" />
    </div>
  );
}
