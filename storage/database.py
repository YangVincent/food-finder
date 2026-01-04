"""Database connection and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import DATABASE_URL
from storage.models import Base, Company


# Create engine and session factory
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)
    print(f"Database initialized: {DATABASE_URL}")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def add_company(session: Session, company_data: dict) -> Company:
    """Add a new company to the database."""
    company = Company(**company_data)
    session.add(company)
    return company


def get_company_by_name_and_state(
    session: Session, name: str, state: str
) -> Company | None:
    """Find a company by name and state (for deduplication)."""
    return (
        session.query(Company)
        .filter(Company.name == name, Company.state == state)
        .first()
    )


def get_companies_needing_enrichment(
    session: Session, limit: int = 100
) -> list[Company]:
    """Get companies that haven't been enriched yet."""
    return (
        session.query(Company)
        .filter(Company.last_enriched_at.is_(None))
        .filter(Company.is_qualified == True)
        .limit(limit)
        .all()
    )


def get_qualified_leads(
    session: Session, min_score: float = 0, limit: int = 1000
) -> list[Company]:
    """Get qualified leads sorted by score."""
    return (
        session.query(Company)
        .filter(Company.is_qualified == True)
        .filter(Company.score >= min_score)
        .order_by(Company.score.desc())
        .limit(limit)
        .all()
    )


def get_lead_stats(session: Session) -> dict:
    """Get statistics about the leads database."""
    total = session.query(Company).count()
    qualified = session.query(Company).filter(Company.is_qualified == True).count()
    with_email = session.query(Company).filter(Company.email.isnot(None)).count()
    with_phone = session.query(Company).filter(Company.phone.isnot(None)).count()
    enriched = session.query(Company).filter(Company.last_enriched_at.isnot(None)).count()

    return {
        "total": total,
        "qualified": qualified,
        "with_email": with_email,
        "with_phone": with_phone,
        "enriched": enriched,
    }
