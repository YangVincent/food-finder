export interface Lead {
  id: number;
  name: string;
  email: string | null;
  phone: string | null;
  website: string | null;
  linkedin_url: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  country: string | null;
  employee_count: number | null;
  description: string | null;
  source: string | null;
  source_id: string | null;
  has_crm: boolean | null;
  tech_stack: string | null;
  has_job_postings: boolean | null;
  has_linkedin: boolean | null;
  company_type: string | null;
  score: number | null;
  is_qualified: boolean | null;
  disqualification_reason: string | null;
  created_at: string | null;
  updated_at: string | null;
  last_enriched_at: string | null;
}

export interface LeadListItem {
  id: number;
  name: string;
  email: string | null;
  phone: string | null;
  website: string | null;
  city: string | null;
  state: string | null;
  source: string | null;
  score: number | null;
  is_qualified: boolean | null;
  has_crm: boolean | null;
  has_linkedin: boolean | null;
  company_type: string | null;
  last_enriched_at: string | null;
}

export interface LeadsResponse {
  leads: LeadListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface StatsResponse {
  total: number;
  qualified: number;
  disqualified: number;
  with_email: number;
  with_phone: number;
  with_website: number;
  enriched: number;
  not_enriched: number;
  enrichment_percentage: number;
}

export interface ScoreDistribution {
  range: string;
  min_score: number;
  max_score: number;
  count: number;
}

export interface FilterOptions {
  states: string[];
  sources: string[];
  company_types: string[];
  score_min: number;
  score_max: number;
}

export interface LeadsQueryParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  state?: string;
  source?: string;
  min_score?: number;
  max_score?: number;
  is_qualified?: boolean;
  has_email?: boolean;
  is_us?: boolean;
  is_enriched?: boolean;
  company_type?: string;
  has_linkedin?: boolean;
  search?: string;
}
