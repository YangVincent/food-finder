"""
USDA Organic Integrity Database API Scraper.

Uses the official USDA API bulk download to fetch certified organic operations.
API docs: https://organic.ams.usda.gov/integrity/Developer/APIHelp.aspx

The bulk download provides 76,000+ operations with ~50% having phone/email data.
"""

from __future__ import annotations

import asyncio
import io
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator, Generator, Optional

import httpx

from config import (
    USDA_API_KEY,
    USDA_API_BASE_URL,
    get_random_delay,
    get_random_user_agent,
)


@dataclass
class USDAOperation:
    """Represents a certified organic operation from USDA API."""

    name: str
    operation_id: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    contact_name: str | None = None
    status: str = "Certified"
    certifier: str | None = None
    other_names: str | None = None


class USDAAPIScraper:
    """Scraper using the official USDA Organic Integrity API."""

    BATCH_SIZE = 100  # API pagination size

    def __init__(self):
        self.client: httpx.AsyncClient | None = None
        self.api_url = f"{USDA_API_BASE_URL}/Operations?api_key={USDA_API_KEY}"
        self.count_url = f"{USDA_API_BASE_URL}/Operations/Count?api_key={USDA_API_KEY}"

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "User-Agent": get_random_user_agent(),
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def get_operations_count(
        self, states: list[str] | None = None, max_retries: int = 3
    ) -> int:
        """Get total count of operations for given states."""
        if not self.client:
            raise RuntimeError("Scraper not initialized. Use async with.")

        payload = {
            "countries": [],  # Empty = all countries
            "states": states or [],
            "fromDate": None,
            "toDate": None,
        }

        for attempt in range(max_retries):
            try:
                await asyncio.sleep(get_random_delay())
                response = await self.client.post(self.count_url, json=payload)
                response.raise_for_status()
                data = response.json()
                # API may return int or {"count": int, "success": bool}
                if isinstance(data, int):
                    return data
                if isinstance(data, dict):
                    return data.get("count", 0)
                return 0
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 503:
                    print(f"  API unavailable (attempt {attempt + 1}/{max_retries}), retrying...")
                    await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
                    continue
                print(f"Error getting count: {e}")
                return 0
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  Connection error (attempt {attempt + 1}/{max_retries}), retrying...")
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                print(f"Error getting count: {e}")
                return 0
        return 0

    async def search_operations(
        self,
        states: list[str] | None = None,
        start_idx: int = 0,
        count: int = 100,
        max_retries: int = 3,
    ) -> list[dict]:
        """
        Fetch operations from the API.

        Args:
            states: List of state codes (e.g., ["CA", "TX"])
            start_idx: Starting index for pagination
            count: Number of records to fetch
            max_retries: Maximum retry attempts

        Returns:
            List of operation dictionaries
        """
        if not self.client:
            raise RuntimeError("Scraper not initialized. Use async with.")

        payload = {
            "countries": [],  # Empty = all countries
            "states": states or [],
            "fromDate": None,
            "toDate": None,
            "startIdx": start_idx,
            "count": count,
        }

        for attempt in range(max_retries):
            try:
                response = await self.client.post(self.api_url, json=payload)
                response.raise_for_status()
                data = response.json()

                # API returns {"operations": [...], "success": true/false}
                if isinstance(data, dict):
                    if not data.get("success", True):
                        print(f"  API error: {data.get('errorMessage', 'Unknown error')}")
                        return []
                    return data.get("operations", []) or []
                return data if isinstance(data, list) else []

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 503:
                    print(f"  API unavailable (attempt {attempt + 1}/{max_retries}), retrying...")
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                print(f"HTTP error fetching operations: {e.response.status_code}")
                return []
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  Connection error (attempt {attempt + 1}/{max_retries}), retrying...")
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                print(f"Error fetching operations: {e}")
                return []
        return []

    def _parse_operation(self, data: dict) -> USDAOperation | None:
        """Parse API response into USDAOperation dataclass."""
        try:
            name = data.get("op_name", "").strip()
            if not name:
                return None

            # Build contact name from first/last
            contact_parts = []
            if data.get("op_contFirstName"):
                contact_parts.append(data["op_contFirstName"].strip())
            if data.get("op_contLastName"):
                contact_parts.append(data["op_contLastName"].strip())
            contact_name = " ".join(contact_parts) if contact_parts else None

            # Build full address
            address_parts = []
            if data.get("opPA_line1"):
                address_parts.append(data["opPA_line1"].strip())
            if data.get("opPA_line2"):
                address_parts.append(data["opPA_line2"].strip())
            address = ", ".join(address_parts) if address_parts else None

            return USDAOperation(
                name=name,
                operation_id=data.get("op_nopOpID", ""),
                address=address,
                city=data.get("opPA_city", "").strip() or None,
                state=data.get("opPA_state", "").strip() or None,
                zip_code=data.get("opPA_zip", "").strip() or None,
                phone=data.get("op_phone", "").strip() or None,
                email=data.get("op_email", "").strip() or None,
                website=data.get("op_url", "").strip() or None,
                contact_name=contact_name,
                status=data.get("op_status", "Certified"),
                certifier=data.get("op_certifierName", "").strip() or None,
                other_names=data.get("op_otherNames", "").strip() or None,
            )
        except Exception as e:
            print(f"Error parsing operation: {e}")
            return None

    async def scrape_by_states(
        self,
        states: list[str] | None = None,
        max_leads: int | None = None,
    ) -> AsyncGenerator[USDAOperation, None]:
        """
        Scrape operations for given states.

        Args:
            states: List of state codes. None = all US states.
            max_leads: Maximum number of leads to return.

        Yields:
            USDAOperation objects
        """
        if not self.client:
            raise RuntimeError("Scraper not initialized. Use async with.")

        state_str = ", ".join(states) if states else "all states"

        # Try to get total count first
        total = await self.get_operations_count(states)
        if total > 0:
            print(f"Found {total} operations for {state_str}")
        else:
            print(f"Fetching operations for {state_str} (count unavailable)...")
            # If count fails, we'll paginate until we get empty results
            total = 1000000  # Large number, will stop when batch is empty

        # Paginate through results
        yielded = 0
        start_idx = 0
        consecutive_failures = 0

        while start_idx < total:
            if max_leads and yielded >= max_leads:
                break

            # Rate limit between API calls
            await asyncio.sleep(get_random_delay())

            # Fetch batch
            batch = await self.search_operations(
                states=states,
                start_idx=start_idx,
                count=self.BATCH_SIZE,
            )

            if not batch:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    print("  Too many consecutive failures, stopping...")
                    break
                continue

            consecutive_failures = 0

            for item in batch:
                if max_leads and yielded >= max_leads:
                    break

                operation = self._parse_operation(item)
                if operation:
                    yielded += 1
                    yield operation

            start_idx += self.BATCH_SIZE
            if total < 1000000:
                print(f"  Processed {min(start_idx, total)}/{total} operations...")
            else:
                print(f"  Processed {start_idx} operations so far ({yielded} valid)...")

            # If batch was smaller than requested, we're done
            if len(batch) < self.BATCH_SIZE:
                break

        print(f"Scraped {yielded} operations total.")


class USDABulkDownloader:
    """Download and parse the USDA bulk XML data dump."""

    BULK_URL = f"{USDA_API_BASE_URL}/GetAllOperationsPublicData?api_key={USDA_API_KEY}"
    CACHE_FILE = Path("/tmp/usda_data/stream")

    def __init__(self, use_cache: bool = True):
        self.client: httpx.Client | None = None
        self.use_cache = use_cache

    def __enter__(self):
        self.client = httpx.Client(
            timeout=300.0,  # 5 min timeout for large download
            follow_redirects=True,
            headers={"User-Agent": get_random_user_agent()},
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()

    def download_and_parse(
        self,
        states: list[str] | None = None,
        max_leads: int | None = None,
    ) -> Generator[USDAOperation, None, None]:
        """
        Download bulk XML and parse operations.

        Args:
            states: Filter to these state codes (e.g., ["CA", "TX"]). None = all.
            max_leads: Maximum operations to yield.

        Yields:
            USDAOperation objects
        """
        if not self.client:
            raise RuntimeError("Downloader not initialized. Use with statement.")

        xml_content = None

        # Check for cached file first
        if self.use_cache and self.CACHE_FILE.exists():
            cache_age_hours = (Path("/tmp").stat().st_mtime - self.CACHE_FILE.stat().st_mtime) / 3600
            if cache_age_hours < 24:  # Cache valid for 24 hours
                print(f"Using cached USDA data ({self.CACHE_FILE})")
                xml_content = self.CACHE_FILE.read_bytes()

        if xml_content is None:
            print("Downloading USDA bulk data (this may take a minute)...")

            # Download ZIP file with retry logic
            max_retries = 3
            response = None
            for attempt in range(max_retries):
                try:
                    response = self.client.get(self.BULK_URL)
                    response.raise_for_status()
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 503 and attempt < max_retries - 1:
                        wait = 10 * (attempt + 1)
                        print(f"  API unavailable, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                        import time
                        time.sleep(wait)
                        continue
                    raise
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait = 10 * (attempt + 1)
                        print(f"  Connection error, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                        import time
                        time.sleep(wait)
                        continue
                    raise

            if not response:
                raise RuntimeError("Failed to download USDA data after retries")

            print(f"Downloaded {len(response.content) / 1024 / 1024:.1f} MB")

            # Extract ZIP in memory
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                # The ZIP contains a single file named "stream"
                xml_content = zf.read("stream")

            # Save to cache
            self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.CACHE_FILE.write_bytes(xml_content)
            print(f"Cached to {self.CACHE_FILE}")

        print("Parsing XML data...")

        # Parse XML
        yielded = 0
        state_set = set(s.upper() for s in states) if states else None

        # Use iterparse for memory efficiency
        context = ET.iterparse(io.BytesIO(xml_content), events=("end",))

        for event, elem in context:
            if elem.tag != "Operation":
                continue

            if max_leads and yielded >= max_leads:
                break

            operation = self._parse_xml_operation(elem)

            # Clear element to free memory
            elem.clear()

            if not operation:
                continue

            # Filter by state if specified
            if state_set:
                if not operation.state:
                    continue
                op_state = operation.state.upper()
                if op_state not in state_set:
                    continue

            yielded += 1
            yield operation

            if yielded % 1000 == 0:
                print(f"  Processed {yielded} operations...")

        print(f"Parsed {yielded} operations total.")

    def _parse_xml_operation(self, elem: ET.Element) -> USDAOperation | None:
        """Parse an Operation XML element."""
        try:
            name = self._get_text(elem, "op_name")
            if not name:
                return None

            # Build contact name
            first = self._get_text(elem, "op_contFirstName")
            last = self._get_text(elem, "op_contLastName")
            contact_name = " ".join(filter(None, [first, last])) or None

            # Build address
            line1 = self._get_text(elem, "opPA_line1")
            line2 = self._get_text(elem, "opPA_line2")
            address = ", ".join(filter(None, [line1, line2])) or None

            # Get state - convert full name to abbreviation if needed
            state = self._get_text(elem, "opPA_state")
            if state:
                state = self._normalize_state(state)

            return USDAOperation(
                name=name,
                operation_id=self._get_text(elem, "op_nopOpID") or "",
                address=address,
                city=self._get_text(elem, "opPA_city"),
                state=state,
                zip_code=self._get_text(elem, "opPA_zip"),
                phone=self._get_text(elem, "op_phone"),
                email=self._get_text(elem, "op_email"),
                website=self._get_text(elem, "op_url"),
                contact_name=contact_name,
                status=self._get_text(elem, "op_status") or "Certified",
                certifier=self._get_text(elem, "op_certifierName"),
                other_names=self._get_text(elem, "op_otherNames"),
            )
        except Exception as e:
            return None

    def _get_text(self, elem: ET.Element, tag: str) -> str | None:
        """Get text content of a child element."""
        child = elem.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None

    def _normalize_state(self, state: str) -> str:
        """Convert full state name to abbreviation."""
        state_map = {
            "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
            "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
            "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
            "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
            "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
            "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
            "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
            "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
            "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
            "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
            "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
            "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
            "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
        }
        state_lower = state.lower()
        return state_map.get(state_lower, state[:2].upper() if len(state) > 2 else state.upper())


def scrape_bulk(
    states: list[str] | None = None,
    max_leads: int | None = None,
) -> Generator[USDAOperation, None, None]:
    """
    Scrape organic operations using bulk XML download (recommended).

    This is more reliable than the paginated API and provides all data at once.

    Args:
        states: List of state codes to filter. None = all states.
        max_leads: Maximum number of leads to return.

    Yields:
        USDAOperation objects
    """
    with USDABulkDownloader() as downloader:
        for operation in downloader.download_and_parse(states, max_leads):
            yield operation


async def scrape_all_states(
    states: list[str] | None = None,
    max_leads: int | None = None,
) -> AsyncGenerator[USDAOperation, None]:
    """
    Scrape organic operations from USDA API (uses bulk download).

    Args:
        states: List of state codes to scrape. None = all US states.
        max_leads: Maximum number of leads to scrape.

    Yields:
        USDAOperation objects
    """
    # Use synchronous bulk download (more reliable than async paginated API)
    for operation in scrape_bulk(states, max_leads):
        yield operation


if __name__ == "__main__":
    # Test the scraper
    print("Testing USDA bulk downloader...")
    count = 0
    with_contact = 0

    for op in scrape_bulk(states=["VT"], max_leads=20):
        has_contact = bool(op.phone or op.email)
        if has_contact:
            with_contact += 1
        print(f"  {op.name}")
        print(f"    City: {op.city}, {op.state}")
        print(f"    Phone: {op.phone or '-'}")
        print(f"    Email: {op.email or '-'}")
        print(f"    Website: {op.website or '-'}")
        print()
        count += 1

    print(f"Total: {count} ({with_contact} with contact info)")
