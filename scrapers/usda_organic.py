"""
USDA Organic Integrity Database Scraper.

Fetches certified organic operations from the USDA database.
Uses the web search interface since the API requires special access.
"""

import asyncio
import re
from dataclasses import dataclass
from typing import AsyncGenerator

import httpx
from bs4 import BeautifulSoup

from config import get_random_delay, get_random_user_agent


@dataclass
class OrganicOperation:
    """Represents a certified organic operation from USDA."""

    name: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    certifier: str | None = None
    certificate_number: str | None = None
    scope: str | None = None  # Crops, Livestock, Handling, etc.
    status: str = "Certified"


class USDAOrganicScraper:
    """Scraper for the USDA Organic Integrity Database."""

    BASE_URL = "https://organic.ams.usda.gov/integrity"
    SEARCH_URL = f"{BASE_URL}/Search"

    def __init__(self):
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": get_random_user_agent()},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def search_by_state(
        self, state: str, scope: str = "All"
    ) -> AsyncGenerator[OrganicOperation, None]:
        """
        Search for organic operations by state.

        Args:
            state: Two-letter state code (e.g., "CA", "TX")
            scope: Filter by scope - "All", "Crops", "Livestock", "Handling", "Wild Crops"

        Yields:
            OrganicOperation objects
        """
        if not self.client:
            raise RuntimeError("Scraper not initialized. Use async with.")

        # The USDA site uses a POST-based search form
        # We'll need to simulate form submission
        search_params = {
            "State": state,
            "Scope": scope,
            "Status": "Certified",
        }

        try:
            # First get the search page to extract any CSRF tokens if needed
            response = await self.client.get(self.SEARCH_URL)
            response.raise_for_status()

            # Rate limit
            await asyncio.sleep(get_random_delay())

            # Parse results
            async for operation in self._parse_search_results(response.text, state):
                yield operation

        except httpx.HTTPError as e:
            print(f"HTTP error searching state {state}: {e}")

    async def _parse_search_results(
        self, html: str, state: str
    ) -> AsyncGenerator[OrganicOperation, None]:
        """Parse search results HTML and yield operations."""
        soup = BeautifulSoup(html, "lxml")

        # Look for operation rows in the results table
        # Note: The actual HTML structure may need adjustment based on the real page
        result_rows = soup.select("table.results tr, .operation-card, .result-item")

        for row in result_rows:
            operation = self._parse_operation_row(row, state)
            if operation:
                yield operation

    def _parse_operation_row(
        self, element: BeautifulSoup, default_state: str
    ) -> OrganicOperation | None:
        """Parse a single operation from search results."""
        try:
            # Extract text content
            text = element.get_text(separator=" ", strip=True)
            if not text or len(text) < 10:
                return None

            # Try to extract company name (usually the first major text element)
            name_elem = element.select_one("td:first-child, .name, h3, h4, strong")
            name = name_elem.get_text(strip=True) if name_elem else None

            if not name:
                # Fallback: use first line of text
                lines = text.split("\n")
                name = lines[0].strip() if lines else None

            if not name:
                return None

            # Extract address components
            address = self._extract_address(text)
            city, state, zip_code = self._parse_city_state_zip(text)

            # Extract phone
            phone = self._extract_phone(text)

            # Extract email
            email = self._extract_email(element)

            return OrganicOperation(
                name=name,
                address=address,
                city=city,
                state=state or default_state,
                zip_code=zip_code,
                phone=phone,
                email=email,
            )
        except Exception as e:
            print(f"Error parsing operation: {e}")
            return None

    def _extract_address(self, text: str) -> str | None:
        """Extract street address from text."""
        # Look for common address patterns
        address_pattern = r"\d+\s+[\w\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Way|Ct|Court)"
        match = re.search(address_pattern, text, re.IGNORECASE)
        return match.group(0) if match else None

    def _parse_city_state_zip(self, text: str) -> tuple[str | None, str | None, str | None]:
        """Extract city, state, and zip from text."""
        # Pattern: City, ST 12345
        pattern = r"([A-Za-z\s]+),\s*([A-Z]{2})\s*(\d{5}(?:-\d{4})?)"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip(), match.group(2), match.group(3)
        return None, None, None

    def _extract_phone(self, text: str) -> str | None:
        """Extract phone number from text."""
        # Common US phone patterns
        patterns = [
            r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            r"\d{3}-\d{3}-\d{4}",
            r"\d{10}",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def _extract_email(self, element: BeautifulSoup) -> str | None:
        """Extract email from HTML element."""
        # Check for mailto links
        mailto = element.select_one('a[href^="mailto:"]')
        if mailto:
            href = mailto.get("href", "")
            return href.replace("mailto:", "").split("?")[0]

        # Check for email pattern in text
        text = element.get_text()
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(email_pattern, text)
        return match.group(0) if match else None


async def scrape_all_states(
    states: list[str] | None = None,
) -> AsyncGenerator[OrganicOperation, None]:
    """
    Scrape organic operations from all US states.

    Args:
        states: List of state codes to scrape. Defaults to all 50 states.

    Yields:
        OrganicOperation objects
    """
    if states is None:
        states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ]

    async with USDAOrganicScraper() as scraper:
        for state in states:
            print(f"Scraping state: {state}")
            async for operation in scraper.search_by_state(state):
                yield operation

            # Rate limit between states
            await asyncio.sleep(get_random_delay())


# Alternative: Use the downloadable CSV if available
async def fetch_data_export() -> list[dict] | None:
    """
    Attempt to fetch the USDA data export if available.

    The USDA periodically publishes CSV exports of the full database.
    This is more reliable than scraping if available.
    """
    export_url = "https://organic.ams.usda.gov/integrity/api/reports/clients"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            headers = {"User-Agent": get_random_user_agent()}
            response = await client.get(export_url, headers=headers)

            if response.status_code == 200:
                # Try to parse as JSON
                try:
                    return response.json()
                except Exception:
                    pass

                # Try to parse as CSV
                # (would need csv module)
                pass

            return None
        except Exception as e:
            print(f"Could not fetch data export: {e}")
            return None


if __name__ == "__main__":
    # Test the scraper
    async def main():
        print("Testing USDA Organic scraper...")
        count = 0
        async for op in scrape_all_states(["CA"]):  # Just test California
            print(f"Found: {op.name} - {op.city}, {op.state}")
            count += 1
            if count >= 10:
                break
        print(f"Total found: {count}")

    asyncio.run(main())
