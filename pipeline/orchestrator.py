"""
Pipeline orchestrator.

Coordinates the full scrape -> enrich -> score workflow.
"""

import asyncio
from datetime import datetime

from storage.database import (
    get_session,
    add_company,
    get_company_by_name_and_state,
    get_lead_stats,
)
from storage.models import Company
from scrapers.usda_organic import scrape_all_states, OrganicOperation
from scrapers.usda_api import scrape_all_states as scrape_usda_api, USDAOperation
from scrapers.google_search import WebsiteFinder
from enrichers.contact_extractor import ContactExtractor
from enrichers.tech_detector import TechDetector
from enrichers.company_classifier import CompanyClassifier
from pipeline.scorer import score_company_dict
from config import is_source_enabled, get_enabled_sources


async def run_scrape_pipeline(
    states: list[str] | None = None,
    max_leads: int | None = None,
) -> int:
    """
    Run the full scraping pipeline for USDA organic operations.

    Args:
        states: List of state codes to scrape (default: all 50)
        max_leads: Maximum number of leads to scrape (default: unlimited)

    Returns:
        Number of leads scraped
    """
    count = 0
    duplicates = 0

    print(f"Starting scrape pipeline...")
    if states:
        print(f"States: {', '.join(states)}")

    async for operation in scrape_all_states(states):
        with get_session() as session:
            # Check for duplicates
            existing = get_company_by_name_and_state(
                session, operation.name, operation.state or ""
            )
            if existing:
                duplicates += 1
                continue

            # Add to database
            company_data = {
                "name": operation.name,
                "address": operation.address,
                "city": operation.city,
                "state": operation.state,
                "zip_code": operation.zip_code,
                "phone": operation.phone,
                "email": operation.email,
                "website": operation.website,
                "source": "usda_organic",
                "source_id": operation.certificate_number,
            }
            add_company(session, company_data)
            count += 1

            if count % 100 == 0:
                print(f"Scraped {count} leads...")

            if max_leads and count >= max_leads:
                break

    print(f"\nScrape complete!")
    print(f"  New leads: {count}")
    print(f"  Duplicates skipped: {duplicates}")

    return count


async def run_usda_api_pipeline(
    states: list[str] | None = None,
    max_leads: int | None = None,
) -> int:
    """
    Run the scraping pipeline using the official USDA API.

    This is the preferred method as it provides direct access to
    phone, email, and website data without needing enrichment.

    Args:
        states: List of state codes to scrape (default: all 50)
        max_leads: Maximum number of leads to scrape (default: unlimited)

    Returns:
        Number of leads scraped
    """
    count = 0
    duplicates = 0
    with_contact = 0

    print(f"Starting USDA API scrape pipeline...")
    if states:
        print(f"States: {', '.join(states)}")

    async for operation in scrape_usda_api(states, max_leads):
        with get_session() as session:
            # Check for duplicates
            existing = get_company_by_name_and_state(
                session, operation.name, operation.state or ""
            )
            if existing:
                duplicates += 1
                continue

            # Add to database with full contact info from API
            company_data = {
                "name": operation.name,
                "address": operation.address,
                "city": operation.city,
                "state": operation.state,
                "zip_code": operation.zip_code,
                "country": operation.country,
                "phone": operation.phone,
                "email": operation.email,
                "website": operation.website,
                "source": "usda_api",
                "source_id": operation.operation_id,
                "description": operation.contact_name,  # Store contact name in description
            }
            add_company(session, company_data)
            count += 1

            # Track contact info coverage
            if operation.phone or operation.email:
                with_contact += 1

            if count % 100 == 0:
                print(f"Scraped {count} leads ({with_contact} with contact info)...")

            if max_leads and count >= max_leads:
                break

    print(f"\nUSDA API scrape complete!")
    print(f"  New leads: {count}")
    print(f"  With phone/email: {with_contact} ({100*with_contact//max(count,1)}%)")
    print(f"  Duplicates skipped: {duplicates}")

    return count


def _company_to_dict(company: Company) -> dict:
    """Convert a Company object to a dictionary while in session."""
    return {
        "id": company.id,
        "name": company.name,
        "website": company.website,
        "email": company.email,
        "phone": company.phone,
        "linkedin_url": company.linkedin_url,
        "address": company.address,
        "city": company.city,
        "state": company.state,
        "zip_code": company.zip_code,
        "employee_count": company.employee_count,
        "has_crm": company.has_crm,
        "tech_stack": company.tech_stack,
        "score": company.score,
        "is_qualified": company.is_qualified,
        "source": company.source,
    }


async def run_enrichment_pipeline(
    batch_size: int = 50,
    max_leads: int | None = None,
) -> int:
    """
    Run the enrichment pipeline for leads that need enrichment.

    Args:
        batch_size: Number of leads to process per batch
        max_leads: Maximum total leads to enrich

    Returns:
        Number of leads enriched
    """
    enriched_count = 0

    print("Starting enrichment pipeline...")

    while True:
        # Get companies needing enrichment and convert to dicts
        # Only enrich US leads (international leads less likely to convert)
        company_dicts = []
        with get_session() as session:
            companies = (
                session.query(Company)
                .filter(Company.last_enriched_at.is_(None))
                .filter(Company.is_qualified == True)
                .filter(Company.country == "USA")
                .limit(batch_size)
                .all()
            )

            if not companies:
                print("No more companies to enrich.")
                break

            # Convert to dicts while still in session
            company_dicts = [_company_to_dict(c) for c in companies]
            print(f"Enriching batch of {len(company_dicts)} companies...")

        # Enrich outside the session
        # Track which companies were actually enriched
        enriched_ids = set()

        async with WebsiteFinder() as website_finder, \
                   ContactExtractor() as contact_extractor, \
                   TechDetector() as tech_detector:

            for company in company_dicts:
                try:
                    print(f"  Enriching: {company['name'][:50]}...")

                    # Find website if missing
                    if not company["website"]:
                        website = await website_finder.find_website(
                            company["name"], company["city"], company["state"]
                        )
                        if website:
                            company["website"] = website
                            print(f"    Found website: {website[:50]}")

                        # Find LinkedIn
                        linkedin = await website_finder.find_linkedin(
                            company["name"], company["city"], company["state"]
                        )
                        if linkedin:
                            company["linkedin_url"] = linkedin
                            print(f"    Found LinkedIn: {linkedin[:50]}")

                    # Extract contacts from website
                    if company["website"]:
                        contacts = await contact_extractor.extract_from_website(
                            company["website"]
                        )
                        if contacts.emails and not company["email"]:
                            company["email"] = contacts.emails[0]
                            print(f"    Found email: {company['email']}")
                        if contacts.phones and not company["phone"]:
                            company["phone"] = contacts.phones[0]
                            print(f"    Found phone: {company['phone']}")

                        # Detect tech stack
                        tech = await tech_detector.analyze_website(company["website"])
                        company["has_crm"] = tech.has_crm
                        company["crm_detected"] = tech.crm_detected  # Save CRM name for disqualification reason
                        company["tech_stack"] = str(tech.detected_tech) if tech.detected_tech else None
                        if tech.has_crm:
                            print(f"    CRM detected: {tech.crm_detected}")

                    # Find LinkedIn if not already found
                    if not company.get("linkedin_url"):
                        linkedin = await website_finder.find_linkedin(
                            company["name"], company["city"], company["state"]
                        )
                        if linkedin:
                            company["linkedin_url"] = linkedin
                            print(f"    Found LinkedIn: {linkedin[:50]}")

                    # Classify company type
                    classifier = CompanyClassifier()
                    classification = classifier.classify(
                        name=company["name"],
                        website=company.get("website"),
                        linkedin_url=company.get("linkedin_url"),
                        has_crm=company.get("has_crm"),
                        tech_stack=company.get("tech_stack"),
                        employee_count=company.get("employee_count"),
                    )
                    company["company_type"] = classification.company_type.value
                    company["has_linkedin"] = classification.has_linkedin
                    print(f"    Type: {classification.company_type.value} ({classification.confidence})")

                    # Score the lead
                    score_company_dict(company)
                    print(f"    Score: {company['score']}")

                    # Mark this company as actually enriched
                    enriched_ids.add(company["id"])
                    enriched_count += 1

                except Exception as e:
                    print(f"    Error: {e}")

                if max_leads and enriched_count >= max_leads:
                    break

        # Save updates back to database - only for actually enriched leads
        with get_session() as session:
            for company in company_dicts:
                if company["id"] not in enriched_ids:
                    continue  # Skip leads that weren't actually enriched

                db_company = session.query(Company).filter(Company.id == company["id"]).first()
                if db_company:
                    db_company.website = company.get("website")
                    db_company.linkedin_url = company.get("linkedin_url")
                    db_company.email = company.get("email")
                    db_company.phone = company.get("phone")
                    db_company.has_crm = company.get("has_crm")
                    db_company.tech_stack = company.get("tech_stack")
                    db_company.has_linkedin = company.get("has_linkedin")
                    db_company.company_type = company.get("company_type")
                    db_company.score = company.get("score", 0)
                    db_company.is_qualified = company.get("is_qualified", True)
                    db_company.disqualification_reason = company.get("disqualification_reason")
                    db_company.last_enriched_at = datetime.utcnow()

        if max_leads and enriched_count >= max_leads:
            break

    # Print final stats
    with get_session() as session:
        stats = get_lead_stats(session)
        print(f"\nEnrichment complete!")
        print(f"  Total leads: {stats['total']}")
        print(f"  Qualified: {stats['qualified']}")
        print(f"  With email: {stats['with_email']}")
        print(f"  With phone: {stats['with_phone']}")

    return enriched_count


async def run_full_pipeline(
    states: list[str] | None = None,
    max_scrape: int | None = None,
    max_enrich: int | None = None,
) -> None:
    """
    Run the complete pipeline: scrape -> enrich -> score.

    Args:
        states: States to scrape
        max_scrape: Maximum leads to scrape
        max_enrich: Maximum leads to enrich
    """
    print("=" * 50)
    print("FOOD-FINDER - Lead Generation Pipeline")
    print("=" * 50)

    # Step 1: Scrape
    print("\n[STEP 1] Scraping USDA Organic Database...")
    await run_scrape_pipeline(states, max_scrape)

    # Step 2: Enrich
    print("\n[STEP 2] Enriching leads...")
    await run_enrichment_pipeline(max_leads=max_enrich)

    print("\n" + "=" * 50)
    print("Pipeline complete!")
    print("=" * 50)


if __name__ == "__main__":
    # Test run
    asyncio.run(run_full_pipeline(states=["VT"], max_scrape=10, max_enrich=5))
