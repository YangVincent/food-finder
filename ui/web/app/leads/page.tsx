'use client';

import { Suspense, useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  Search,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Mail,
  Phone,
  Globe,
  ExternalLink,
  X,
} from 'lucide-react';
import { getLeads, getFilterOptions } from '@/lib/api';
import { cn, getScoreClass } from '@/lib/utils';
import type { LeadsQueryParams } from '@/lib/types';

function LeadsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Parse URL params into state
  const params: LeadsQueryParams = useMemo(() => ({
    page: parseInt(searchParams.get('page') || '1'),
    page_size: 50,
    sort_by: searchParams.get('sort_by') || 'score',
    sort_order: (searchParams.get('sort_order') || 'desc') as 'asc' | 'desc',
    state: searchParams.get('state') || undefined,
    source: searchParams.get('source') || undefined,
    is_qualified: searchParams.get('is_qualified') === 'true' ? true :
                  searchParams.get('is_qualified') === 'false' ? false : undefined,
    is_us: searchParams.get('is_us') === 'false' ? false :
           searchParams.get('is_us') === 'all' ? undefined : true,  // Default to US only
    is_enriched: searchParams.get('is_enriched') === 'true' ? true :
                 searchParams.get('is_enriched') === 'false' ? false : undefined,
    search: searchParams.get('search') || undefined,
  }), [searchParams]);

  const [searchInput, setSearchInput] = useState(params.search || '');

  // Fetch data
  const { data: leadsData, isLoading } = useQuery({
    queryKey: ['leads', params],
    queryFn: () => getLeads(params),
  });

  const { data: filterOptions } = useQuery({
    queryKey: ['filter-options'],
    queryFn: getFilterOptions,
  });

  // Update URL params
  const updateParams = useCallback((newParams: Partial<LeadsQueryParams>) => {
    const current = new URLSearchParams(searchParams.toString());

    Object.entries(newParams).forEach(([key, value]) => {
      if (value === undefined || value === '') {
        current.delete(key);
      } else {
        current.set(key, String(value));
      }
    });

    // Reset to page 1 when filters change (except when explicitly changing page)
    if (!('page' in newParams)) {
      current.set('page', '1');
    }

    router.push(`/leads?${current.toString()}`);
  }, [router, searchParams]);

  // Handle sort
  const handleSort = (column: string) => {
    if (params.sort_by === column) {
      updateParams({ sort_order: params.sort_order === 'asc' ? 'desc' : 'asc' });
    } else {
      updateParams({ sort_by: column, sort_order: 'desc' });
    }
  };

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    updateParams({ search: searchInput || undefined });
  };

  // Clear all filters
  const clearFilters = () => {
    setSearchInput('');
    router.push('/leads');
  };

  // is_us=true is the default, so count as "active filter" if set to false or all (undefined)
  const hasActiveFilters = params.state || params.source || params.is_qualified !== undefined || params.is_us !== true || params.is_enriched !== undefined || params.search;

  const SortIndicator = ({ column }: { column: string }) => {
    if (params.sort_by !== column) return null;
    return params.sort_order === 'asc' ? (
      <ChevronUp className="h-3 w-3" />
    ) : (
      <ChevronDown className="h-3 w-3" />
    );
  };

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      {/* Header */}
      <div className="mb-6 animate-slide-up opacity-0">
        <div className="flex items-end gap-3">
          <h1 className="font-mono text-2xl font-bold tracking-tight text-[var(--text-primary)]">
            LEADS
          </h1>
          <div className="h-1 w-12 bg-[var(--accent-primary)] mb-2" />
        </div>
        <p className="mt-2 font-mono text-sm text-[var(--text-tertiary)]">
          {leadsData ? `${leadsData.total.toLocaleString()} leads found` : 'Loading...'}
        </p>
      </div>

      {/* Filters Bar */}
      <div className="mb-6 border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4 animate-slide-up opacity-0 stagger-1">
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-muted)]" />
              <input
                type="text"
                placeholder="Search leads..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] pl-10 pr-4 py-2 font-mono text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:border-[var(--accent-primary)] focus:outline-none transition-colors"
              />
            </div>
          </form>

          {/* State Filter */}
          <select
            value={params.state || ''}
            onChange={(e) => updateParams({ state: e.target.value || undefined })}
            className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] px-3 py-2 font-mono text-sm text-[var(--text-primary)] focus:border-[var(--accent-primary)] focus:outline-none"
          >
            <option value="">All States</option>
            {filterOptions?.states.map((state) => (
              <option key={state} value={state}>
                {state}
              </option>
            ))}
          </select>

          {/* Source Filter */}
          <select
            value={params.source || ''}
            onChange={(e) => updateParams({ source: e.target.value || undefined })}
            className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] px-3 py-2 font-mono text-sm text-[var(--text-primary)] focus:border-[var(--accent-primary)] focus:outline-none"
          >
            <option value="">All Sources</option>
            {filterOptions?.sources.map((source) => (
              <option key={source} value={source}>
                {source}
              </option>
            ))}
          </select>

          {/* Qualified Filter */}
          <select
            value={params.is_qualified === undefined ? '' : String(params.is_qualified)}
            onChange={(e) => updateParams({
              is_qualified: e.target.value === '' ? undefined : e.target.value === 'true'
            })}
            className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] px-3 py-2 font-mono text-sm text-[var(--text-primary)] focus:border-[var(--accent-primary)] focus:outline-none"
          >
            <option value="">All Status</option>
            <option value="true">Qualified</option>
            <option value="false">Disqualified</option>
          </select>

          {/* US Filter - defaults to US Only */}
          <select
            value={params.is_us === undefined ? 'all' : String(params.is_us)}
            onChange={(e) => updateParams({
              is_us: e.target.value as any  // Pass 'all', 'true', or 'false' as string
            })}
            className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] px-3 py-2 font-mono text-sm text-[var(--text-primary)] focus:border-[var(--accent-primary)] focus:outline-none"
          >
            <option value="true">US Only</option>
            <option value="false">International</option>
            <option value="all">All Countries</option>
          </select>

          {/* Enriched Filter */}
          <select
            value={params.is_enriched === undefined ? '' : String(params.is_enriched)}
            onChange={(e) => updateParams({
              is_enriched: e.target.value === '' ? undefined : e.target.value === 'true'
            })}
            className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] px-3 py-2 font-mono text-sm text-[var(--text-primary)] focus:border-[var(--accent-primary)] focus:outline-none"
          >
            <option value="">All Enrichment</option>
            <option value="true">Enriched</option>
            <option value="false">Not Enriched</option>
          </select>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-2 px-3 py-2 font-mono text-xs text-[var(--danger)] hover:bg-[var(--danger)]/10 transition-colors"
            >
              <X className="h-3 w-3" />
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)] animate-slide-up opacity-0 stagger-2">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
                {[
                  { key: 'name', label: 'Company', sortable: true },
                  { key: 'city', label: 'Location', sortable: false },
                  { key: 'state', label: 'State', sortable: true },
                  { key: 'contact', label: 'Contact', sortable: false },
                  { key: 'source', label: 'Source', sortable: false },
                  { key: 'score', label: 'Score', sortable: true },
                  { key: 'status', label: 'Status', sortable: false },
                  { key: 'actions', label: '', sortable: false },
                ].map((col) => (
                  <th
                    key={col.key}
                    className={cn(
                      'px-4 py-3 text-left font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)]',
                      col.sortable && 'cursor-pointer hover:text-[var(--text-primary)] transition-colors'
                    )}
                    onClick={() => col.sortable && handleSort(col.key)}
                  >
                    <div className="flex items-center gap-1">
                      {col.label}
                      {col.sortable && <SortIndicator column={col.key} />}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                // Loading skeleton
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i} className="border-b border-[var(--border-subtle)]">
                    {Array.from({ length: 8 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="skeleton h-4 w-full max-w-[120px]" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : leadsData?.leads.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center">
                    <p className="font-mono text-sm text-[var(--text-tertiary)]">
                      No leads found matching your criteria
                    </p>
                  </td>
                </tr>
              ) : (
                leadsData?.leads.map((lead) => (
                  <tr
                    key={lead.id}
                    className="border-b border-[var(--border-subtle)] table-row-hover"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/leads/${lead.id}`}
                        className="font-medium text-[var(--text-primary)] hover:text-[var(--accent-primary)] transition-colors"
                      >
                        {lead.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <span className="data-cell text-[var(--text-secondary)]">
                        {lead.city || '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="data-cell text-[var(--text-secondary)]">
                        {lead.state || '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {lead.email && (
                          <Mail className="h-3.5 w-3.5 text-[var(--success)]" />
                        )}
                        {lead.phone && (
                          <Phone className="h-3.5 w-3.5 text-[var(--info)]" />
                        )}
                        {lead.website && (
                          <Globe className="h-3.5 w-3.5 text-[var(--text-tertiary)]" />
                        )}
                        {!lead.email && !lead.phone && !lead.website && (
                          <span className="data-cell text-[var(--text-muted)]">—</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="data-cell text-[var(--text-tertiary)]">
                        {lead.source || '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={cn(
                          'inline-flex items-center px-2 py-0.5 font-mono text-xs font-medium',
                          getScoreClass(lead.score)
                        )}
                      >
                        {lead.score?.toFixed(0) || '0'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {lead.is_qualified ? (
                        <span className="inline-flex items-center px-2 py-0.5 font-mono text-xs font-medium bg-[var(--success)]/15 text-[var(--success)]">
                          Qualified
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 font-mono text-xs font-medium bg-[var(--danger)]/15 text-[var(--danger)]">
                          Disqualified
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/leads/${lead.id}`}
                        className="text-[var(--text-muted)] hover:text-[var(--accent-primary)] transition-colors"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {leadsData && leadsData.total_pages > 1 && (
          <div className="flex items-center justify-between border-t border-[var(--border-subtle)] px-4 py-3">
            <div className="font-mono text-xs text-[var(--text-muted)]">
              Page {leadsData.page} of {leadsData.total_pages}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => updateParams({ page: leadsData.page - 1 })}
                disabled={leadsData.page <= 1}
                className={cn(
                  'flex items-center gap-1 px-3 py-1.5 font-mono text-xs transition-colors',
                  leadsData.page <= 1
                    ? 'text-[var(--text-muted)] cursor-not-allowed'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                )}
              >
                <ChevronLeft className="h-3 w-3" />
                Previous
              </button>
              <button
                onClick={() => updateParams({ page: leadsData.page + 1 })}
                disabled={leadsData.page >= leadsData.total_pages}
                className={cn(
                  'flex items-center gap-1 px-3 py-1.5 font-mono text-xs transition-colors',
                  leadsData.page >= leadsData.total_pages
                    ? 'text-[var(--text-muted)] cursor-not-allowed'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                )}
              >
                Next
                <ChevronRight className="h-3 w-3" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function LeadsPageFallback() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <div className="mb-6">
        <div className="skeleton h-8 w-32 mb-2" />
        <div className="skeleton h-4 w-48" />
      </div>
      <div className="skeleton h-16 w-full mb-6" />
      <div className="skeleton h-96 w-full" />
    </div>
  );
}

export default function LeadsPage() {
  return (
    <Suspense fallback={<LeadsPageFallback />}>
      <LeadsContent />
    </Suspense>
  );
}
