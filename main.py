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
from pipeline.orchestrator import run_scrape_pipeline, run_enrichment_pipeline, run_full_pipeline
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
        help="Maximum number of leads to scrape"
    ),
):
    """Scrape leads from USDA Organic Database."""
    init_db()

    state_list = None
    if states:
        state_list = [s.strip().upper() for s in states.split(",")]
        console.print(f"Scraping states: {', '.join(state_list)}")

    asyncio.run(run_scrape_pipeline(state_list, max_leads))


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
def stats():
    """Show lead database statistics."""
    init_db()
    print_lead_summary()


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


if __name__ == "__main__":
    app()
