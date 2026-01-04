"""
Website finder using web search.

Tries multiple search methods to find company websites.
"""

import asyncio
import re
from urllib.parse import quote_plus, urlparse, unquote

import httpx
from bs4 import BeautifulSoup

from config import get_random_delay, get_random_user_agent


class WebsiteFinder:
    """Find company websites using web search."""

    def __init__(self):
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def find_website(
        self, company_name: str, city: str | None = None, state: str | None = None
    ) -> str | None:
        """
        Find a company's website using search.

        Args:
            company_name: Name of the company
            city: City for more specific results
            state: State for more specific results

        Returns:
            Website URL or None if not found
        """
        if not self.client:
            raise RuntimeError("Finder not initialized. Use async with.")

        # Try DuckDuckGo lite first
        result = await self._search_ddg_lite(company_name, city, state)
        if result:
            return result

        # Fallback: try Bing
        result = await self._search_bing(company_name, city, state)
        if result:
            return result

        return None

    async def find_linkedin(
        self, company_name: str, city: str | None = None, state: str | None = None
    ) -> str | None:
        """
        Find a company's LinkedIn page.
        """
        if not self.client:
            raise RuntimeError("Finder not initialized. Use async with.")

        # Build search query targeting LinkedIn
        query = f'site:linkedin.com/company {company_name}'
        if state:
            query += f" {state}"

        results = await self._search_bing(company_name, city, state, site="linkedin.com/company")
        return results

    async def _search_ddg_lite(
        self, company_name: str, city: str | None, state: str | None
    ) -> str | None:
        """Search using DuckDuckGo Lite."""
        if not self.client:
            return None

        query_parts = [company_name]
        if city:
            query_parts.append(city)
        if state:
            query_parts.append(state)
        query = " ".join(query_parts)

        await asyncio.sleep(get_random_delay())

        try:
            # Use the lite version
            url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
            response = await self.client.get(url)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "lxml")

            # Look for result links
            for link in soup.select("a.result-link, td a[href*='://']"):
                href = link.get("href", "")
                if href and self._is_valid_company_url(href, company_name):
                    return href

            # Also check for uddg redirect links
            for link in soup.select("a[href*='uddg=']"):
                href = link.get("href", "")
                match = re.search(r"uddg=([^&]+)", href)
                if match:
                    actual_url = unquote(match.group(1))
                    if self._is_valid_company_url(actual_url, company_name):
                        return actual_url

        except Exception as e:
            pass

        return None

    async def _search_bing(
        self, company_name: str, city: str | None, state: str | None, site: str | None = None
    ) -> str | None:
        """Search using Bing."""
        if not self.client:
            return None

        query_parts = [company_name]
        if city:
            query_parts.append(city)
        if state:
            query_parts.append(state)
        if site:
            query_parts.insert(0, f"site:{site}")
        query = " ".join(query_parts)

        await asyncio.sleep(get_random_delay())

        try:
            url = f"https://www.bing.com/search?q={quote_plus(query)}"
            response = await self.client.get(url)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "lxml")

            # Look for organic search results
            for link in soup.select("li.b_algo h2 a, .b_algo a"):
                href = link.get("href", "")
                if href and href.startswith("http"):
                    if site:
                        if site in href:
                            return href
                    elif self._is_valid_company_url(href, company_name):
                        return href

        except Exception as e:
            pass

        return None

    def _is_valid_company_url(self, url: str, company_name: str) -> bool:
        """Check if URL looks like a company website (not a directory)."""
        # Sites to exclude
        excluded_domains = {
            "facebook.com", "twitter.com", "instagram.com", "linkedin.com",
            "youtube.com", "yelp.com", "yellowpages.com", "bbb.org",
            "manta.com", "dnb.com", "zoominfo.com", "crunchbase.com",
            "bloomberg.com", "wikipedia.org", "amazon.com", "walmart.com",
            "chamberofcommerce.com", "indeed.com", "glassdoor.com",
            "mapquest.com", "google.com", "bing.com", "duckduckgo.com",
        }

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www prefix
            if domain.startswith("www."):
                domain = domain[4:]

            # Skip excluded domains
            for excluded in excluded_domains:
                if excluded in domain:
                    return False

            # Skip obvious directory/search pages
            path = parsed.path.lower()
            if any(x in path for x in ["/search", "/directory", "/results", "/find"]):
                return False

            return True

        except Exception:
            return False


async def find_websites_for_companies(companies: list[dict]) -> list[dict]:
    """
    Find websites for a list of companies.

    Args:
        companies: List of dicts with 'name', 'city', 'state' keys

    Returns:
        Same list with 'website' and 'linkedin_url' keys added
    """
    async with WebsiteFinder() as finder:
        for company in companies:
            name = company.get("name", "")
            city = company.get("city")
            state = company.get("state")

            # Find website
            website = await finder.find_website(name, city, state)
            company["website"] = website

            # Find LinkedIn
            linkedin = await finder.find_linkedin(name, city, state)
            company["linkedin_url"] = linkedin

            # Rate limit
            await asyncio.sleep(get_random_delay())

    return companies


if __name__ == "__main__":
    # Test the finder
    async def main():
        async with WebsiteFinder() as finder:
            # Test with known companies
            for name, city in [
                ("Blue Bottle Coffee", "Berkeley"),
                ("Bird Rock Coffee Roasters", "San Diego"),
                ("Canyon Coffee", "Los Angeles"),
            ]:
                website = await finder.find_website(name, city, "CA")
                print(f"{name}: {website}")

    asyncio.run(main())
