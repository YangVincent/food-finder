"""SQLAlchemy models for lead storage."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Company(Base):
    """A company lead in the database."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic info
    name = Column(String(500), nullable=False, index=True)
    website = Column(String(500))

    # Contact info
    email = Column(String(255))
    phone = Column(String(50))
    linkedin_url = Column(String(500))

    # Location
    address = Column(Text)
    city = Column(String(255))
    state = Column(String(50), index=True)
    zip_code = Column(String(20))
    country = Column(String(100))

    # Company details
    employee_count = Column(Integer)
    description = Column(Text)

    # Source tracking
    source = Column(String(100), index=True)  # e.g., "usda_organic", "state_ca"
    source_id = Column(String(255))  # Original ID from source

    # Enrichment data
    has_crm = Column(Boolean)
    tech_stack = Column(Text)  # JSON string of detected technologies
    has_job_postings = Column(Boolean)
    has_linkedin = Column(Boolean)
    company_type = Column(String(50), index=True)  # research_institution, government, company, established_business, artisan_shop, farm, unknown

    # Scoring
    score = Column(Float, default=0.0, index=True)
    is_qualified = Column(Boolean, default=True)
    disqualification_reason = Column(String(255))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_enriched_at = Column(DateTime)

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}', state='{self.state}')>"

    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        return {
            "id": self.id,
            "name": self.name,
            "website": self.website,
            "email": self.email,
            "phone": self.phone,
            "linkedin_url": self.linkedin_url,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "employee_count": self.employee_count,
            "source": self.source,
            "score": self.score,
            "is_qualified": self.is_qualified,
            "has_linkedin": self.has_linkedin,
            "company_type": self.company_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
