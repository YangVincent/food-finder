"""
California Organic Processors data loader.

Loads data from the CDPH RegisteredOrganic.xlsx file.
Source: https://www.cdph.ca.gov/Programs/CEH/DFDCS/Pages/FDBPrograms/FoodSafetyProgram/OrganicFoodProcessors.aspx
"""

import httpx
from pathlib import Path

import pandas as pd

from storage.database import get_session, add_company, get_company_by_name_and_state
from storage.models import Company


DATA_URL = "https://www.cdph.ca.gov/Programs/CEH/DFDCS/CDPH%20Document%20Library/FDB/FoodSafetyProgram/Organic/RegisteredOrganic.xlsx"
DATA_FILE = Path(__file__).parent.parent / "data" / "ca_organic_processors.xlsx"


def download_data(force: bool = False) -> Path:
    """Download the CA organic processors Excel file if not present."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    if DATA_FILE.exists() and not force:
        print(f"Using cached data: {DATA_FILE}")
        return DATA_FILE

    print(f"Downloading CA organic processors data...")
    response = httpx.get(DATA_URL, follow_redirects=True, timeout=60.0)
    response.raise_for_status()

    DATA_FILE.write_bytes(response.content)
    print(f"Downloaded to: {DATA_FILE}")
    return DATA_FILE


def load_processors(limit: int | None = None) -> list[dict]:
    """
    Load processors from the Excel file.

    Args:
        limit: Maximum number of records to load (default: all)

    Returns:
        List of company dictionaries
    """
    download_data()

    # Read Excel, skip first row (it's repeated headers)
    df = pd.read_excel(DATA_FILE, header=0)

    # The actual headers are in row 0
    df.columns = ["business_name", "dba", "license_type", "license_status", "city"]

    # Skip the header row that's in the data
    df = df[df["business_name"] != "Business Name"]

    # Filter to only registered/active
    df = df[df["license_status"].str.contains("REGISTERED", case=False, na=False)]

    companies = []
    for _, row in df.iterrows():
        # Use DBA name if different and non-empty
        name = row["dba"] if pd.notna(row["dba"]) and row["dba"] != row["business_name"] else row["business_name"]

        company = {
            "name": str(name).strip() if pd.notna(name) else str(row["business_name"]).strip(),
            "legal_name": str(row["business_name"]).strip() if pd.notna(row["business_name"]) else None,
            "city": str(row["city"]).strip().title() if pd.notna(row["city"]) else None,
            "state": "CA",
            "source": "cdph_organic",
            "license_type": str(row["license_type"]).strip() if pd.notna(row["license_type"]) else None,
        }
        companies.append(company)

        if limit and len(companies) >= limit:
            break

    return companies


def import_to_database(limit: int | None = None) -> int:
    """
    Import CA processors to the database.

    Args:
        limit: Maximum number to import

    Returns:
        Number of new records added
    """
    companies = load_processors(limit)
    added = 0
    skipped = 0

    with get_session() as session:
        for company in companies:
            # Check for duplicates
            existing = get_company_by_name_and_state(
                session, company["name"], company["state"]
            )
            if existing:
                skipped += 1
                continue

            # Add to database
            add_company(session, {
                "name": company["name"],
                "city": company["city"],
                "state": company["state"],
                "source": company["source"],
            })
            added += 1

            if added % 100 == 0:
                print(f"Added {added} companies...")

    print(f"\nImport complete!")
    print(f"  Added: {added}")
    print(f"  Skipped (duplicates): {skipped}")

    return added


if __name__ == "__main__":
    # Test loading
    companies = load_processors(limit=10)
    for c in companies:
        print(f"{c['name']} - {c['city']}, {c['state']}")

    print(f"\nTotal would load: {len(load_processors())}")
