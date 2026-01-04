'use client';

import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  X,
  Loader2,
  Copy,
  Check,
  Mail,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
} from 'lucide-react';
import { generateDraftEmail } from '@/lib/api';
import type { DraftEmailResponse, EnrichedCompanyInfo } from '@/lib/types';
import { cn } from '@/lib/utils';

interface DraftEmailModalProps {
  isOpen: boolean;
  onClose: () => void;
  leadId: number;
  leadName: string;
}

export function DraftEmailModal({
  isOpen,
  onClose,
  leadId,
  leadName,
}: DraftEmailModalProps) {
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [enrichedInfo, setEnrichedInfo] = useState<EnrichedCompanyInfo | null>(null);
  const [copied, setCopied] = useState<'subject' | 'body' | 'all' | null>(null);
  const [showEnrichedInfo, setShowEnrichedInfo] = useState(false);

  const mutation = useMutation({
    mutationFn: () => generateDraftEmail(leadId),
    onSuccess: (data: DraftEmailResponse) => {
      setSubject(data.subject);
      setBody(data.body);
      setEnrichedInfo(data.enriched_info);
    },
  });

  // Trigger generation when modal opens
  useEffect(() => {
    if (isOpen && !mutation.isPending && !mutation.data) {
      mutation.mutate();
    }
  }, [isOpen]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setSubject('');
      setBody('');
      setEnrichedInfo(null);
      setCopied(null);
      setShowEnrichedInfo(false);
      mutation.reset();
    }
  }, [isOpen]);

  const copyToClipboard = async (text: string, type: 'subject' | 'body' | 'all') => {
    await navigator.clipboard.writeText(text);
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
  };

  const copyAll = () => {
    const fullEmail = `Subject: ${subject}\n\n${body}`;
    copyToClipboard(fullEmail, 'all');
  };

  if (!isOpen) return null;

  const hasEnrichedContent =
    enrichedInfo &&
    (enrichedInfo.about_text ||
      enrichedInfo.products.length > 0 ||
      enrichedInfo.services.length > 0 ||
      enrichedInfo.key_phrases.length > 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-hidden bg-[var(--bg-primary)] border border-[var(--border-subtle)] shadow-2xl animate-fade-in mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center bg-[var(--accent-primary)]/15">
              <Mail className="h-4 w-4 text-[var(--accent-primary)]" />
            </div>
            <div>
              <h2 className="font-mono text-sm font-bold text-[var(--text-primary)]">
                Draft Email
              </h2>
              <p className="font-mono text-xs text-[var(--text-muted)]">
                {leadName}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-120px)]">
          {mutation.isPending ? (
            <div className="flex flex-col items-center justify-center py-16">
              <Loader2 className="h-8 w-8 text-[var(--accent-primary)] animate-spin mb-4" />
              <p className="font-mono text-sm text-[var(--text-secondary)]">
                Researching company...
              </p>
              <p className="font-mono text-xs text-[var(--text-muted)] mt-1">
                This may take 10-30 seconds
              </p>
            </div>
          ) : mutation.isError ? (
            <div className="flex flex-col items-center justify-center py-16 px-6">
              <AlertTriangle className="h-8 w-8 text-[var(--danger)] mb-4" />
              <p className="font-mono text-sm text-[var(--danger)] text-center">
                Failed to generate email
              </p>
              <p className="font-mono text-xs text-[var(--text-muted)] mt-2 text-center max-w-md">
                {mutation.error?.message || 'An unexpected error occurred'}
              </p>
              <button
                onClick={() => mutation.mutate()}
                className="mt-4 px-4 py-2 font-mono text-sm bg-[var(--bg-elevated)] text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors"
              >
                Try Again
              </button>
            </div>
          ) : (
            <div className="p-6 space-y-4">
              {/* Enriched Info (Collapsible) */}
              {hasEnrichedContent && (
                <div className="border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
                  <button
                    onClick={() => setShowEnrichedInfo(!showEnrichedInfo)}
                    className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-[var(--bg-hover)] transition-colors"
                  >
                    <span className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)]">
                      Company Research
                    </span>
                    {showEnrichedInfo ? (
                      <ChevronUp className="h-4 w-4 text-[var(--text-muted)]" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-[var(--text-muted)]" />
                    )}
                  </button>
                  {showEnrichedInfo && (
                    <div className="px-4 pb-4 space-y-3 border-t border-[var(--border-subtle)]">
                      {enrichedInfo.about_text && (
                        <div className="pt-3">
                          <p className="font-mono text-xs text-[var(--text-muted)] mb-1">About</p>
                          <p className="font-mono text-sm text-[var(--text-secondary)] leading-relaxed">
                            {enrichedInfo.about_text}
                          </p>
                        </div>
                      )}
                      {enrichedInfo.products.length > 0 && (
                        <div>
                          <p className="font-mono text-xs text-[var(--text-muted)] mb-1">Products</p>
                          <div className="flex flex-wrap gap-1">
                            {enrichedInfo.products.map((product, i) => (
                              <span
                                key={i}
                                className="px-2 py-0.5 font-mono text-xs bg-[var(--bg-elevated)] text-[var(--text-secondary)]"
                              >
                                {product}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {enrichedInfo.services.length > 0 && (
                        <div>
                          <p className="font-mono text-xs text-[var(--text-muted)] mb-1">Services</p>
                          <div className="flex flex-wrap gap-1">
                            {enrichedInfo.services.map((service, i) => (
                              <span
                                key={i}
                                className="px-2 py-0.5 font-mono text-xs bg-[var(--bg-elevated)] text-[var(--text-secondary)]"
                              >
                                {service}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {enrichedInfo.key_phrases.length > 0 && (
                        <div>
                          <p className="font-mono text-xs text-[var(--text-muted)] mb-1">Key Topics</p>
                          <div className="flex flex-wrap gap-1">
                            {enrichedInfo.key_phrases.map((phrase, i) => (
                              <span
                                key={i}
                                className="px-2 py-0.5 font-mono text-xs bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]"
                              >
                                {phrase}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Subject Line */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)]">
                    Subject
                  </label>
                  <button
                    onClick={() => copyToClipboard(subject, 'subject')}
                    className="flex items-center gap-1 px-2 py-1 font-mono text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                  >
                    {copied === 'subject' ? (
                      <>
                        <Check className="h-3 w-3 text-[var(--success)]" />
                        <span className="text-[var(--success)]">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full px-3 py-2 font-mono text-sm bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                  placeholder="Email subject..."
                />
              </div>

              {/* Email Body */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="font-mono text-xs uppercase tracking-wider text-[var(--text-tertiary)]">
                    Body
                  </label>
                  <button
                    onClick={() => copyToClipboard(body, 'body')}
                    className="flex items-center gap-1 px-2 py-1 font-mono text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                  >
                    {copied === 'body' ? (
                      <>
                        <Check className="h-3 w-3 text-[var(--success)]" />
                        <span className="text-[var(--success)]">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
                <textarea
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  rows={10}
                  className="w-full px-3 py-2 font-mono text-sm bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)] resize-none leading-relaxed"
                  placeholder="Email body..."
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {!mutation.isPending && !mutation.isError && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <button
              onClick={() => mutation.mutate()}
              className="px-4 py-2 font-mono text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              Regenerate
            </button>
            <button
              onClick={copyAll}
              className={cn(
                'flex items-center gap-2 px-4 py-2 font-mono text-sm transition-colors',
                copied === 'all'
                  ? 'bg-[var(--success)] text-white'
                  : 'bg-[var(--accent-primary)] text-white hover:bg-[var(--accent-primary)]/90'
              )}
            >
              {copied === 'all' ? (
                <>
                  <Check className="h-4 w-4" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4" />
                  Copy All
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
