"""Statistics endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from storage.models import Company
from storage.database import get_lead_stats
from ui.api.dependencies import get_db
from ui.api.schemas import StatsResponse, ScoreDistribution

router = APIRouter()


@router.get("/overview", response_model=StatsResponse)
def get_stats_overview(db: Session = Depends(get_db)):
    """Get overall lead statistics."""
    stats = get_lead_stats(db)

    total = stats["total"]
    qualified = stats["qualified"]
    with_website = db.query(Company).filter(Company.website.isnot(None)).count()

    enrichment_pct = (stats["enriched"] / total * 100) if total > 0 else 0

    return StatsResponse(
        total=total,
        qualified=qualified,
        disqualified=total - qualified,
        with_email=stats["with_email"],
        with_phone=stats["with_phone"],
        with_website=with_website,
        enriched=stats["enriched"],
        not_enriched=total - stats["enriched"],
        enrichment_percentage=round(enrichment_pct, 1)
    )


@router.get("/score-distribution", response_model=list[ScoreDistribution])
def get_score_distribution(db: Session = Depends(get_db)):
    """Get score distribution in buckets."""
    buckets = [
        (0, 20, "0-20"),
        (21, 40, "21-40"),
        (41, 60, "41-60"),
        (61, 80, "61-80"),
    ]

    results = []
    for min_score, max_score, label in buckets:
        count = db.query(Company).filter(
            Company.score >= min_score,
            Company.score <= max_score
        ).count()
        results.append(ScoreDistribution(
            range=label,
            min_score=min_score,
            max_score=max_score,
            count=count
        ))

    return results
