"""Email draft generation endpoints."""

import asyncio
from fastapi import APIRouter, Depends, HTTPException

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy.orm import Session
from storage.models import Company
from ui.api.dependencies import get_db
from ui.api.schemas import DraftEmailResponse, EnrichedCompanyInfo
from enrichers.website_scraper import scrape_company_website, ScrapedContent
from enrichers.email_generator import generate_outreach_email

router = APIRouter()


@router.post("/{lead_id}/draft", response_model=DraftEmailResponse)
async def generate_draft_email(lead_id: int, db: Session = Depends(get_db)):
    """
    Generate a draft outreach email for a lead.

    1. Fetches lead from database
    2. Scrapes company website for business intelligence
    3. Uses AI to generate personalized email
    4. Returns enriched info and draft email
    """
    # Fetch lead
    lead = db.query(Company).filter(Company.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Build location string
    location = None
    if lead.city and lead.state:
        location = f"{lead.city}, {lead.state}"
    elif lead.city:
        location = lead.city
    elif lead.state:
        location = lead.state

    # Scrape website if available
    scraped_content: ScrapedContent | None = None
    if lead.website:
        try:
            # Run async scraping in thread pool
            scraped_content = await scrape_company_website(lead.website)
        except Exception as e:
            # Continue without scraped content if scraping fails
            print(f"Warning: Failed to scrape {lead.website}: {e}")
            scraped_content = None

    # Generate email using AI
    try:
        email = await asyncio.to_thread(
            generate_outreach_email,
            company_name=lead.name,
            location=location,
            website=lead.website,
            scraped_content=scraped_content,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate email: {str(e)}"
        )

    # Build enriched info response
    enriched_info = EnrichedCompanyInfo(
        about_text=scraped_content.about_text if scraped_content else None,
        products=scraped_content.products if scraped_content else [],
        services=scraped_content.services if scraped_content else [],
        key_phrases=scraped_content.key_phrases if scraped_content else [],
    )

    return DraftEmailResponse(
        lead_id=lead.id,
        lead_name=lead.name,
        enriched_info=enriched_info,
        subject=email.subject,
        body=email.body,
    )
