import type {
  Lead,
  LeadsResponse,
  StatsResponse,
  ScoreDistribution,
  FilterOptions,
  LeadsQueryParams,
  DraftEmailResponse,
} from './types';

const API_BASE = 'http://localhost:8000/api';

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getStatsOverview(): Promise<StatsResponse> {
  return fetchAPI<StatsResponse>('/stats/overview');
}

export async function getScoreDistribution(): Promise<ScoreDistribution[]> {
  return fetchAPI<ScoreDistribution[]>('/stats/score-distribution');
}

export async function getLeads(params: LeadsQueryParams = {}): Promise<LeadsResponse> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set('page', params.page.toString());
  if (params.page_size) searchParams.set('page_size', params.page_size.toString());
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);
  if (params.state) searchParams.set('state', params.state);
  if (params.source) searchParams.set('source', params.source);
  if (params.min_score !== undefined) searchParams.set('min_score', params.min_score.toString());
  if (params.max_score !== undefined) searchParams.set('max_score', params.max_score.toString());
  if (params.is_qualified !== undefined) searchParams.set('is_qualified', params.is_qualified.toString());
  if (params.has_email !== undefined) searchParams.set('has_email', params.has_email.toString());
  if (params.is_us !== undefined) searchParams.set('is_us', params.is_us.toString());
  if (params.is_enriched !== undefined) searchParams.set('is_enriched', params.is_enriched.toString());
  if (params.company_type) searchParams.set('company_type', params.company_type);
  if (params.has_linkedin !== undefined) searchParams.set('has_linkedin', params.has_linkedin.toString());
  if (params.search) searchParams.set('search', params.search);

  const query = searchParams.toString();
  return fetchAPI<LeadsResponse>(`/leads/${query ? `?${query}` : ''}`);
}

export async function getLead(id: number): Promise<Lead> {
  return fetchAPI<Lead>(`/leads/${id}`);
}

export async function getFilterOptions(): Promise<FilterOptions> {
  return fetchAPI<FilterOptions>('/leads/filters/');
}

async function postAPI<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API error: ${res.status} ${errorText}`);
  }
  return res.json();
}

export async function generateDraftEmail(leadId: number): Promise<DraftEmailResponse> {
  return postAPI<DraftEmailResponse>(`/email/${leadId}/draft`);
}
