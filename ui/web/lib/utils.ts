import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat('en-US').format(num);
}

export function formatPercentage(num: number): string {
  return `${num.toFixed(1)}%`;
}

export function formatDate(dateString: string | null): string {
  if (!dateString) return '—';
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function formatDateTime(dateString: string | null): string {
  if (!dateString) return '—';
  return new Date(dateString).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

export function getScoreClass(score: number | null): string {
  if (score === null || score === undefined) return 'score-low';
  if (score >= 60) return 'score-excellent';
  if (score >= 40) return 'score-high';
  if (score >= 20) return 'score-medium';
  return 'score-low';
}

export function getScoreLabel(score: number | null): string {
  if (score === null || score === undefined) return 'N/A';
  if (score >= 60) return 'Excellent';
  if (score >= 40) return 'Good';
  if (score >= 20) return 'Fair';
  return 'Low';
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}

export function parseJsonSafe<T>(str: string | null): T | null {
  if (!str) return null;
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}
