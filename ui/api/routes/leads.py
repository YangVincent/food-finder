"""Leads endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional

# Valid US state codes (including territories)
US_STATES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
    'DC', 'PR', 'VI', 'GU', 'AS', 'MP'  # DC + territories
}

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from storage.models import Company
from ui.api.dependencies import get_db
from ui.api.schemas import LeadsResponse, LeadListItem, LeadDetail, FilterOptions

router = APIRouter()


@router.get("/", response_model=LeadsResponse)
def get_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    sort_by: str = Query("score", pattern="^(name|score|state|city|created_at|last_enriched_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    state: Optional[str] = None,
    source: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    is_qualified: Optional[bool] = None,
    has_email: Optional[bool] = None,
    is_us: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get paginated list of leads with filtering."""
    query = db.query(Company)

    # Apply filters
    if state:
        query = query.filter(Company.state == state)
    if source:
        query = query.filter(Company.source == source)
    if min_score is not None:
        query = query.filter(Company.score >= min_score)
    if max_score is not None:
        query = query.filter(Company.score <= max_score)
    if is_qualified is not None:
        query = query.filter(Company.is_qualified == is_qualified)
    if has_email is not None:
        if has_email:
            query = query.filter(Company.email.isnot(None))
        else:
            query = query.filter(Company.email.is_(None))
    if is_us is not None:
        if is_us:
            query = query.filter(Company.country == "USA")
        else:
            query = query.filter((Company.country != "USA") | Company.country.is_(None))
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Company.name.ilike(search_term),
                Company.city.ilike(search_term),
                Company.email.ilike(search_term)
            )
        )

    # Get total count
    total = query.count()

    # Apply sorting
    sort_column = getattr(Company, sort_by)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    query = query.order_by(sort_column.nulls_last())

    # Apply pagination
    offset = (page - 1) * page_size
    leads = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return LeadsResponse(
        leads=[LeadListItem.model_validate(lead) for lead in leads],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/filters", response_model=FilterOptions)
def get_filter_options(db: Session = Depends(get_db)):
    """Get available filter options."""
    states = db.query(Company.state).distinct().filter(Company.state.isnot(None)).all()
    sources = db.query(Company.source).distinct().filter(Company.source.isnot(None)).all()

    score_stats = db.query(
        func.min(Company.score),
        func.max(Company.score)
    ).first()

    return FilterOptions(
        states=sorted([s[0] for s in states]),
        sources=sorted([s[0] for s in sources]),
        score_min=score_stats[0] or 0,
        score_max=score_stats[1] or 100
    )


@router.get("/{lead_id}", response_model=LeadDetail)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a single lead by ID."""
    lead = db.query(Company).filter(Company.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadDetail.model_validate(lead)
