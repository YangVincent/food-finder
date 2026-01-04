"""Pydantic schemas for API responses."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class LeadListItem(BaseModel):
    """Condensed lead for table display."""
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    source: Optional[str] = None
    score: Optional[float] = None
    is_qualified: Optional[bool] = None
    has_crm: Optional[bool] = None
    has_linkedin: Optional[bool] = None
    company_type: Optional[str] = None
    last_enriched_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeadDetail(BaseModel):
    """Full lead details."""
    id: int
    name: str
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None
    source: Optional[str] = None
    source_id: Optional[str] = None
    has_crm: Optional[bool] = None
    tech_stack: Optional[str] = None
    has_job_postings: Optional[bool] = None
    has_linkedin: Optional[bool] = None
    company_type: Optional[str] = None
    score: Optional[float] = None
    is_qualified: Optional[bool] = None
    disqualification_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_enriched_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeadsResponse(BaseModel):
    """Paginated leads response."""
    leads: List[LeadListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatsResponse(BaseModel):
    """Overall statistics."""
    total: int
    qualified: int
    disqualified: int
    with_email: int
    with_phone: int
    with_website: int
    enriched: int
    not_enriched: int
    enrichment_percentage: float


class ScoreDistribution(BaseModel):
    """Score bucket count."""
    range: str
    min_score: int
    max_score: int
    count: int


class FilterOptions(BaseModel):
    """Available filter options."""
    states: List[str]
    sources: List[str]
    company_types: List[str] = []
    score_min: float
    score_max: float
