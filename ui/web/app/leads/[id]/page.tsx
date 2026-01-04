'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Mail,
  Phone,
  Globe,
  Linkedin,
  MapPin,
  Building2,
  Users,
  Calendar,
  Zap,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Copy,
} from 'lucide-react';
import { getLead } from '@/lib/api';
import { cn, formatDateTime, getScoreClass, getScoreLabel, parseJsonSafe } from '@/lib/utils';

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const { data: lead, isLoading, error } = useQuery({
    queryKey: ['lead', id],
    queryFn: () => getLead(id),
    enabled: !isNaN(id),
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-8">
        <div className="animate-pulse space-y-6">
          <div className="skeleton h-8 w-32" />
          <div className="skeleton h-12 w-64" />
          <div className="skeleton h-64 w-full" />
        </div>
      </div>
    );
  }

  if (error || !lead) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-8">
        <div className="border border-[var(--danger)]/30 bg-[var(--danger)]/5 p-8 text-center">
          <AlertTriangle className="mx-auto h-12 w-12 text-[var(--danger)] mb-4" />
          <h2 className="font-mono text-lg font-bold text-[var(--danger)]">
            Lead Not Found
          </h2>
          <p className="mt-2 font-mono text-sm text-[var(--text-tertiary)]">
            The requested lead could not be found.
          </p>
          <button
            onClick={() => router.push('/leads')}
            className="mt-6 px-4 py-2 font-mono text-sm bg-[var(--bg-elevated)] text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors"
          >
            Back to Leads
          </button>
        </div>
      </div>
    );
  }

  const techStack = parseJsonSafe<string[]>(lead.tech_stack);

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      {/* Back Link */}
      <Link
        href="/leads"
        className="inline-flex items-center gap-2 font-mono text-sm text-[var(--text-tertiary)] hover:text-[var(--accent-primary)] transition-colors mb-6 animate-fade-in"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Leads
      </Link>

      {/* Header */}
      <div className="mb-8 animate-slide-up opacity-0">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="font-mono text-2xl font-bold tracking-tight text-[var(--text-primary)]">
              {lead.name}
            </h1>
            <div className="mt-2 flex items-center gap-4">
              {lead.city && lead.state && (
                <div className="flex items-center gap-1.5 text-[var(--text-tertiary)]">
                  <MapPin className="h-3.5 w-3.5" />
                  <span className="font-mono text-sm">
                    {lead.city}, {lead.state}
                  </span>
                </div>
              )}
              <span className="font-mono text-xs text-[var(--text-muted)]">
                ID: {lead.id}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Score Badge */}
            <div className="text-right">
              <span
                className={cn(
                  'inline-flex items-center px-3 py-1.5 font-mono text-lg font-bold',
                  getScoreClass(lead.score)
                )}
              >
                {lead.score?.toFixed(0) || '0'}
              </span>
              <p className="mt-1 font-mono text-xs text-[var(--text-muted)]">
                {getScoreLabel(lead.score)}
              </p>
            </div>
            {/* Qualified Status */}
            <div className="flex flex-col items-center">
              {lead.is_qualified ? (
                <CheckCircle2 className="h-8 w-8 text-[var(--success)]" />
              ) : (
                <XCircle className="h-8 w-8 text-[var(--danger)]" />
              )}
              <p className="mt-1 font-mono text-xs text-[var(--text-muted)]">
                {lead.is_qualified ? 'Qualified' : 'Disqualified'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Contact Information */}
          <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 animate-slide-up opacity-0 stagger-1">
            <h2 className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-4">
              Contact Information
            </h2>
            <div className="space-y-4">
              {lead.email && (
                <div className="flex items-center justify-between group">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center bg-[var(--success)]/15">
                      <Mail className="h-4 w-4 text-[var(--success)]" />
                    </div>
                    <div>
                      <p className="font-mono text-xs text-[var(--text-muted)]">Email</p>
                      <a
                        href={`mailto:${lead.email}`}
                        className="font-mono text-sm text-[var(--text-primary)] hover:text-[var(--accent-primary)] transition-colors"
                      >
                        {lead.email}
                      </a>
                    </div>
                  </div>
                  <button
                    onClick={() => copyToClipboard(lead.email!)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-all"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                </div>
              )}

              {lead.phone && (
                <div className="flex items-center justify-between group">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center bg-[var(--info)]/15">
                      <Phone className="h-4 w-4 text-[var(--info)]" />
                    </div>
                    <div>
                      <p className="font-mono text-xs text-[var(--text-muted)]">Phone</p>
                      <a
                        href={`tel:${lead.phone}`}
                        className="font-mono text-sm text-[var(--text-primary)] hover:text-[var(--accent-primary)] transition-colors"
                      >
                        {lead.phone}
                      </a>
                    </div>
                  </div>
                  <button
                    onClick={() => copyToClipboard(lead.phone!)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-all"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                </div>
              )}

              {lead.website && (
                <div className="flex items-center justify-between group">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center bg-[var(--text-tertiary)]/15">
                      <Globe className="h-4 w-4 text-[var(--text-tertiary)]" />
                    </div>
                    <div>
                      <p className="font-mono text-xs text-[var(--text-muted)]">Website</p>
                      <a
                        href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-mono text-sm text-[var(--text-primary)] hover:text-[var(--accent-primary)] transition-colors inline-flex items-center gap-1"
                      >
                        {lead.website}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </div>
                </div>
              )}

              {lead.linkedin_url && (
                <div className="flex items-center justify-between group">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center bg-[#0077b5]/15">
                      <Linkedin className="h-4 w-4 text-[#0077b5]" />
                    </div>
                    <div>
                      <p className="font-mono text-xs text-[var(--text-muted)]">LinkedIn</p>
                      <a
                        href={lead.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-mono text-sm text-[var(--text-primary)] hover:text-[var(--accent-primary)] transition-colors inline-flex items-center gap-1"
                      >
                        View Profile
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </div>
                </div>
              )}

              {!lead.email && !lead.phone && !lead.website && !lead.linkedin_url && (
                <p className="font-mono text-sm text-[var(--text-muted)] text-center py-4">
                  No contact information available
                </p>
              )}
            </div>
          </div>

          {/* Location */}
          <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 animate-slide-up opacity-0 stagger-2">
            <h2 className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-4">
              Location
            </h2>
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 items-center justify-center bg-[var(--accent-primary)]/15 flex-shrink-0">
                <MapPin className="h-4 w-4 text-[var(--accent-primary)]" />
              </div>
              <div className="space-y-1">
                {lead.address && (
                  <p className="font-mono text-sm text-[var(--text-primary)]">{lead.address}</p>
                )}
                <p className="font-mono text-sm text-[var(--text-secondary)]">
                  {[lead.city, lead.state, lead.zip_code].filter(Boolean).join(', ')}
                </p>
                {lead.country && (
                  <p className="font-mono text-xs text-[var(--text-muted)]">{lead.country}</p>
                )}
              </div>
            </div>
          </div>

          {/* Description */}
          {lead.description && (
            <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 animate-slide-up opacity-0 stagger-3">
              <h2 className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-4">
                Description
              </h2>
              <p className="font-mono text-sm text-[var(--text-secondary)] leading-relaxed">
                {lead.description}
              </p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Company Details */}
          <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 animate-slide-in-right opacity-0 stagger-1">
            <h2 className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-4">
              Company Details
            </h2>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Building2 className="h-4 w-4 text-[var(--text-muted)]" />
                <div>
                  <p className="font-mono text-xs text-[var(--text-muted)]">Source</p>
                  <p className="font-mono text-sm text-[var(--text-primary)]">
                    {lead.source || '—'}
                  </p>
                </div>
              </div>
              {lead.employee_count && (
                <div className="flex items-center gap-3">
                  <Users className="h-4 w-4 text-[var(--text-muted)]" />
                  <div>
                    <p className="font-mono text-xs text-[var(--text-muted)]">Employees</p>
                    <p className="font-mono text-sm text-[var(--text-primary)]">
                      {lead.employee_count}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Tech Stack */}
          <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 animate-slide-in-right opacity-0 stagger-2">
            <h2 className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-4">
              Technology
            </h2>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-[var(--text-muted)]">Has CRM:</span>
                {lead.has_crm === true ? (
                  <span className="font-mono text-xs text-[var(--danger)]">Yes</span>
                ) : lead.has_crm === false ? (
                  <span className="font-mono text-xs text-[var(--success)]">No</span>
                ) : (
                  <span className="font-mono text-xs text-[var(--text-tertiary)]">Not checked</span>
                )}
              </div>
              {techStack && techStack.length > 0 && (
                <div>
                  <p className="font-mono text-xs text-[var(--text-muted)] mb-2">Detected Tech:</p>
                  <div className="flex flex-wrap gap-1">
                    {techStack.map((tech, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 font-mono text-xs bg-[var(--bg-elevated)] text-[var(--text-secondary)]"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Enrichment Status */}
          <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-5 animate-slide-in-right opacity-0 stagger-3">
            <h2 className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)] mb-4">
              Enrichment
            </h2>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Zap className={cn(
                  'h-4 w-4',
                  lead.last_enriched_at ? 'text-[var(--accent-primary)]' : 'text-[var(--text-muted)]'
                )} />
                <div>
                  <p className="font-mono text-xs text-[var(--text-muted)]">Last Enriched</p>
                  <p className="font-mono text-sm text-[var(--text-primary)]">
                    {formatDateTime(lead.last_enriched_at)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Calendar className="h-4 w-4 text-[var(--text-muted)]" />
                <div>
                  <p className="font-mono text-xs text-[var(--text-muted)]">Created</p>
                  <p className="font-mono text-sm text-[var(--text-primary)]">
                    {formatDateTime(lead.created_at)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Disqualification Reason */}
          {!lead.is_qualified && lead.disqualification_reason && (
            <div className="border border-[var(--danger)]/30 bg-[var(--danger)]/5 p-5 animate-slide-in-right opacity-0 stagger-4">
              <h2 className="font-mono text-xs uppercase tracking-wider text-[var(--danger)] mb-3">
                Disqualification Reason
              </h2>
              <p className="font-mono text-sm text-[var(--text-secondary)]">
                {lead.disqualification_reason}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
