"""
CSV export functionality.

Exports qualified leads to CSV for use in outreach tools.
"""

import csv
from datetime import datetime
from pathlib import Path

from storage.database import get_session, get_qualified_leads, get_lead_stats
from storage.models import Company


def export_leads_to_csv(
    output_path: str | Path | None = None,
    min_score: float = 0,
    limit: int = 1000,
    include_disqualified: bool = False,
) -> Path:
    """
    Export qualified leads to a CSV file.

    Args:
        output_path: Path for the output file. If None, auto-generates.
        min_score: Minimum score to include (default: 0)
        limit: Maximum number of leads to export (default: 1000)
        include_disqualified: Include disqualified leads (default: False)

    Returns:
        Path to the created CSV file
    """
    # Auto-generate filename if not provided
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"leads_export_{timestamp}.csv")
    else:
        output_path = Path(output_path)

    # Define CSV columns
    fieldnames = [
        "name",
        "email",
        "phone",
        "website",
        "linkedin_url",
        "address",
        "city",
        "state",
        "zip_code",
        "employee_count",
        "score",
        "source",
        "has_crm",
        "is_qualified",
    ]

    with get_session() as session:
        # Get leads
        if include_disqualified:
            leads = (
                session.query(Company)
                .filter(Company.score >= min_score)
                .order_by(Company.score.desc())
                .limit(limit)
                .all()
            )
        else:
            leads = get_qualified_leads(session, min_score, limit)

        # Write to CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for lead in leads:
                writer.writerow({
                    "name": lead.name,
                    "email": lead.email,
                    "phone": lead.phone,
                    "website": lead.website,
                    "linkedin_url": lead.linkedin_url,
                    "address": lead.address,
                    "city": lead.city,
                    "state": lead.state,
                    "zip_code": lead.zip_code,
                    "employee_count": lead.employee_count,
                    "score": lead.score,
                    "source": lead.source,
                    "has_crm": lead.has_crm,
                    "is_qualified": lead.is_qualified,
                })

        print(f"Exported {len(leads)} leads to {output_path}")

    return output_path


def export_for_email_outreach(
    output_path: str | Path | None = None,
    min_score: float = 20,
    limit: int = 500,
) -> Path:
    """
    Export leads formatted for email outreach.

    Only includes leads with email addresses.
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"email_leads_{timestamp}.csv")
    else:
        output_path = Path(output_path)

    fieldnames = [
        "company_name",
        "email",
        "first_name",  # Placeholder for personalization
        "city",
        "state",
        "website",
    ]

    with get_session() as session:
        leads = (
            session.query(Company)
            .filter(Company.is_qualified == True)
            .filter(Company.email.isnot(None))
            .filter(Company.score >= min_score)
            .order_by(Company.score.desc())
            .limit(limit)
            .all()
        )

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for lead in leads:
                writer.writerow({
                    "company_name": lead.name,
                    "email": lead.email,
                    "first_name": "",  # To be filled manually or via enrichment
                    "city": lead.city,
                    "state": lead.state,
                    "website": lead.website,
                })

        print(f"Exported {len(leads)} email leads to {output_path}")

    return output_path


def export_for_linkedin_outreach(
    output_path: str | Path | None = None,
    min_score: float = 20,
    limit: int = 500,
) -> Path:
    """
    Export leads formatted for LinkedIn outreach.

    Only includes leads with LinkedIn URLs.
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"linkedin_leads_{timestamp}.csv")
    else:
        output_path = Path(output_path)

    fieldnames = [
        "company_name",
        "linkedin_url",
        "city",
        "state",
        "website",
        "employee_count",
    ]

    with get_session() as session:
        leads = (
            session.query(Company)
            .filter(Company.is_qualified == True)
            .filter(Company.linkedin_url.isnot(None))
            .filter(Company.score >= min_score)
            .order_by(Company.score.desc())
            .limit(limit)
            .all()
        )

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for lead in leads:
                writer.writerow({
                    "company_name": lead.name,
                    "linkedin_url": lead.linkedin_url,
                    "city": lead.city,
                    "state": lead.state,
                    "website": lead.website,
                    "employee_count": lead.employee_count,
                })

        print(f"Exported {len(leads)} LinkedIn leads to {output_path}")

    return output_path


def print_lead_summary() -> None:
    """Print a summary of leads in the database."""
    with get_session() as session:
        stats = get_lead_stats(session)

        print("\n" + "=" * 40)
        print("LEAD DATABASE SUMMARY")
        print("=" * 40)
        print(f"Total leads:     {stats['total']:,}")
        print(f"Qualified:       {stats['qualified']:,}")
        print(f"With email:      {stats['with_email']:,}")
        print(f"With phone:      {stats['with_phone']:,}")
        print(f"Enriched:        {stats['enriched']:,}")
        print("=" * 40)

        # Top leads by score
        top_leads = (
            session.query(Company)
            .filter(Company.is_qualified == True)
            .order_by(Company.score.desc())
            .limit(5)
            .all()
        )

        if top_leads:
            print("\nTop 5 Leads by Score:")
            for i, lead in enumerate(top_leads, 1):
                print(f"  {i}. {lead.name} ({lead.state}) - Score: {lead.score}")
                if lead.email:
                    print(f"     Email: {lead.email}")


if __name__ == "__main__":
    print_lead_summary()
