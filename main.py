#!/usr/bin/env python3
"""
Food-Finder - Lead Generation CLI

Find medium-sized food/ag companies for outreach.
"""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from storage.database import init_db, get_session, get_lead_stats
from storage.models import Company
from pipeline.orchestrator import run_scrape_pipeline, run_enrichment_pipeline, run_full_pipeline, run_usda_api_pipeline
from pipeline.scorer import score_lead
from config import ENABLED_SOURCES, get_enabled_sources, SCORING
from export.csv_export import (
    export_leads_to_csv,
    export_for_email_outreach,
    export_for_linkedin_outreach,
    print_lead_summary,
)
from scrapers.ca_processors import import_to_database as import_ca_processors

app = typer.Typer(help="Food-Finder - Lead generation for food/ag companies")
console = Console()


@app.command()
def init():
    """Initialize the database."""
    init_db()
    console.print("[green]Database initialized![/green]")


@app.command()
def scrape(
    states: Optional[str] = typer.Option(
        None,
        "--states", "-s",
        help="Comma-separated state codes (e.g., CA,TX,NY). Default: all states"
    ),
    max_leads: Optional[int] = typer.Option(
        None,
        "--max", "-m",
        help="Maximum number of leads to scrape (default: unlimited for usda_api)"
    ),
    source: str = typer.Option(
        "usda_api",
        "--source",
        help="Data source: usda_api (recommended), usda_organic, cdph_organic"
    ),
):
    """Scrape leads from specified source."""
    init_db()

    state_list = None
    if states:
        state_list = [s.strip().upper() for s in states.split(",")]
        console.print(f"Scraping states: {', '.join(state_list)}")
    else:
        console.print("Scraping all US states")

    if source == "usda_api":
        console.print("[cyan]Using USDA API bulk download (recommended)[/cyan]")
        if max_leads:
            console.print(f"[dim]Limiting to {max_leads} leads[/dim]")
        asyncio.run(run_usda_api_pipeline(state_list, max_leads))
    elif source == "usda_organic":
        console.print("[yellow]Using USDA web scraper (may be slow/broken)[/yellow]")
        asyncio.run(run_scrape_pipeline(state_list, max_leads))
    elif source == "cdph_organic":
        console.print("[yellow]Using CA CDPH (limited data - name/city only)[/yellow]")
        count = import_ca_processors(limit=max_leads)
        console.print(f"[green]Imported {count} companies[/green]")
    else:
        console.print(f"[red]Unknown source: {source}[/red]")
        console.print("Available sources: usda_api, usda_organic, cdph_organic")


@app.command("import-ca")
def import_ca(
    max_leads: Optional[int] = typer.Option(
        None,
        "--max", "-m",
        help="Maximum number of leads to import"
    ),
):
    """Import California organic food processors (2800+ companies)."""
    init_db()
    console.print("[cyan]Importing California organic processors...[/cyan]")
    count = import_ca_processors(limit=max_leads)
    console.print(f"[green]Imported {count} companies![/green]")


@app.command()
def enrich(
    batch_size: int = typer.Option(
        50,
        "--batch", "-b",
        help="Number of leads to process per batch"
    ),
    max_leads: Optional[int] = typer.Option(
        None,
        "--max", "-m",
        help="Maximum number of leads to enrich"
    ),
):
    """Enrich leads with website, contact info, and tech detection."""
    init_db()
    asyncio.run(run_enrichment_pipeline(batch_size, max_leads))


@app.command()
def run(
    states: Optional[str] = typer.Option(
        None,
        "--states", "-s",
        help="Comma-separated state codes"
    ),
    max_scrape: Optional[int] = typer.Option(
        None,
        "--max-scrape",
        help="Maximum leads to scrape"
    ),
    max_enrich: Optional[int] = typer.Option(
        None,
        "--max-enrich",
        help="Maximum leads to enrich"
    ),
):
    """Run the full pipeline: scrape -> enrich -> score."""
    init_db()

    state_list = None
    if states:
        state_list = [s.strip().upper() for s in states.split(",")]

    asyncio.run(run_full_pipeline(state_list, max_scrape, max_enrich))


@app.command()
def sources():
    """Show available data sources and their status."""
    table = Table(title="Available Data Sources")
    table.add_column("Source", style="cyan")
    table.add_column("Enabled")
    table.add_column("Description")

    source_info = {
        "usda_api": ("Yes" if ENABLED_SOURCES.get("usda_api") else "No", "USDA Official API - has phone, email, website"),
        "usda_organic": ("Yes" if ENABLED_SOURCES.get("usda_organic") else "No", "USDA web scraper - broken (JS-heavy site)"),
        "cdph_organic": ("Yes" if ENABLED_SOURCES.get("cdph_organic") else "No", "CA CDPH processors - minimal data (name/city only)"),
    }

    for src, (enabled, desc) in source_info.items():
        style = "green" if enabled == "Yes" else "dim"
        table.add_row(src, f"[{style}]{enabled}[/{style}]", desc)

    console.print(table)
    console.print("\nUse [cyan]--source[/cyan] flag with scrape command to specify source.")


@app.command()
def stats():
    """Show lead database statistics."""
    init_db()
    print_lead_summary()

    # Also show by source
    with get_session() as session:
        from sqlalchemy import func
        source_counts = (
            session.query(Company.source, func.count(Company.id))
            .group_by(Company.source)
            .all()
        )
        if source_counts:
            console.print("\n[bold]Leads by source:[/bold]")
            for src, count in source_counts:
                console.print(f"  {src or 'unknown'}: {count}")


@app.command()
def score(
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Re-score all leads, not just unscored ones"
    ),
):
    """Score all leads based on available data (email, phone, website)."""
    init_db()

    with get_session() as session:
        # Get leads to score
        if force:
            leads = session.query(Company).all()
            console.print(f"[cyan]Re-scoring all {len(leads)} leads...[/cyan]")
        else:
            leads = session.query(Company).filter(Company.score == 0).all()
            console.print(f"[cyan]Scoring {len(leads)} unscored leads...[/cyan]")

        if not leads:
            console.print("[yellow]No leads to score.[/yellow]")
            return

        scored = 0
        score_distribution = {0: 0, 5: 0, 10: 0, 15: 0, 20: 0, 25: 0, 30: 0}

        for lead in leads:
            # Calculate score based on available data
            new_score = 0.0

            if lead.email:
                new_score += SCORING["email_found"]  # +15
            if lead.phone:
                new_score += SCORING["phone_found"]  # +10
            if lead.website:
                new_score += SCORING["has_website"]  # +5
                new_score += SCORING["basic_website"]  # +5 (assume basic until enriched)

            # Update the lead
            lead.score = new_score
            scored += 1

            # Track distribution
            bucket = int(new_score // 5) * 5
            if bucket > 30:
                bucket = 30
            score_distribution[bucket] = score_distribution.get(bucket, 0) + 1

            if scored % 10000 == 0:
                console.print(f"  Scored {scored} leads...")

        session.commit()

        console.print(f"\n[green]Scored {scored} leads![/green]")
        console.print("\n[bold]Score distribution:[/bold]")
        for score_val in sorted(score_distribution.keys()):
            count = score_distribution[score_val]
            if count > 0:
                bar = "█" * min(50, count // 500)
                console.print(f"  {score_val:2d} pts: {count:,} {bar}")


@app.command()
def export(
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Output file path"
    ),
    min_score: float = typer.Option(
        0,
        "--min-score",
        help="Minimum score to include"
    ),
    limit: int = typer.Option(
        1000,
        "--limit", "-l",
        help="Maximum number of leads"
    ),
    format: str = typer.Option(
        "all",
        "--format", "-f",
        help="Export format: all, email, linkedin"
    ),
):
    """Export leads to CSV."""
    init_db()

    if format == "email":
        path = export_for_email_outreach(output, min_score, limit)
    elif format == "linkedin":
        path = export_for_linkedin_outreach(output, min_score, limit)
    else:
        path = export_leads_to_csv(output, min_score, limit)

    console.print(f"[green]Exported to {path}[/green]")


@app.command()
def top(
    limit: int = typer.Option(
        10,
        "--limit", "-l",
        help="Number of leads to show"
    ),
    min_score: float = typer.Option(
        0,
        "--min-score",
        help="Minimum score filter"
    ),
):
    """Show top leads by score."""
    init_db()

    with get_session() as session:
        leads = (
            session.query(Company)
            .filter(Company.is_qualified == True)
            .filter(Company.score >= min_score)
            .order_by(Company.score.desc())
            .limit(limit)
            .all()
        )

        if not leads:
            console.print("[yellow]No qualified leads found.[/yellow]")
            return

        table = Table(title=f"Top {len(leads)} Leads")
        table.add_column("Name", style="cyan")
        table.add_column("State")
        table.add_column("Score", justify="right")
        table.add_column("Email")
        table.add_column("Phone")
        table.add_column("Website")

        for lead in leads:
            table.add_row(
                lead.name[:40],
                lead.state or "",
                f"{lead.score:.0f}",
                lead.email or "-",
                lead.phone or "-",
                (lead.website[:30] + "...") if lead.website and len(lead.website) > 30 else (lead.website or "-"),
            )

        console.print(table)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (company name)"),
    state: Optional[str] = typer.Option(
        None,
        "--state", "-s",
        help="Filter by state code"
    ),
):
    """Search for leads by name."""
    init_db()

    with get_session() as session:
        q = session.query(Company).filter(Company.name.ilike(f"%{query}%"))

        if state:
            q = q.filter(Company.state == state.upper())

        leads = q.limit(20).all()

        if not leads:
            console.print(f"[yellow]No leads found matching '{query}'[/yellow]")
            return

        table = Table(title=f"Search Results for '{query}'")
        table.add_column("Name", style="cyan")
        table.add_column("City")
        table.add_column("State")
        table.add_column("Score", justify="right")
        table.add_column("Email")
        table.add_column("Qualified")

        for lead in leads:
            table.add_row(
                lead.name[:40],
                lead.city or "",
                lead.state or "",
                f"{lead.score:.0f}" if lead.score else "-",
                lead.email or "-",
                "Yes" if lead.is_qualified else "No",
            )

        console.print(table)


@app.command("enrich-linkedin")
def enrich_linkedin(
    limit: int = typer.Option(
        100,
        "--limit", "-l",
        help="Maximum number of leads to process (default: 100 to stay within API free tier)"
    ),
):
    """
    Enrich promising companies with LinkedIn URLs.

    Only processes companies that:
    - Have already been enriched
    - Are classified as type 'company'
    - Don't have a LinkedIn URL yet
    """
    init_db()

    async def run_linkedin_enrichment():
        from scrapers.google_search import WebsiteFinder
        from datetime import datetime

        with get_session() as session:
            # Find promising companies without LinkedIn
            companies = (
                session.query(Company)
                .filter(Company.last_enriched_at.isnot(None))  # Already enriched
                .filter(Company.company_type == "company")  # Type is 'company'
                .filter(
                    (Company.linkedin_url.is_(None)) | (Company.linkedin_url == "")
                )  # No LinkedIn yet
                .order_by(Company.score.desc())  # Prioritize high-score leads
                .limit(limit)
                .all()
            )

            if not companies:
                console.print("[yellow]No companies to enrich with LinkedIn.[/yellow]")
                return

            console.print(f"[cyan]Enriching {len(companies)} companies with LinkedIn URLs...[/cyan]")

            found_count = 0
            async with WebsiteFinder() as finder:
                for i, company in enumerate(companies, 1):
                    console.print(f"  [{i}/{len(companies)}] {company.name[:50]}...", end="")

                    linkedin_url = await finder.find_linkedin(
                        company.name, company.city, company.state
                    )

                    if linkedin_url:
                        company.linkedin_url = linkedin_url
                        company.has_linkedin = True
                        found_count += 1
                        console.print(f" [green]✓[/green] {linkedin_url}")
                    else:
                        console.print(" [dim]not found[/dim]")

                    # Small delay to be nice to the API
                    await asyncio.sleep(0.2)

            session.commit()
            console.print(f"\n[green]Done! Found LinkedIn for {found_count}/{len(companies)} companies.[/green]")

    asyncio.run(run_linkedin_enrichment())


if __name__ == "__main__":
    app()
