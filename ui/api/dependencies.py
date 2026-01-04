"""Database session dependency for FastAPI."""

import sys
from pathlib import Path

# Add parent directory to path to import storage module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from storage.database import SessionLocal
from typing import Generator
from sqlalchemy.orm import Session


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
