"""
Website content scraper for business intelligence.

Scrapes company websites to extract products, services, and about information.
"""

import asyncio
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from config import get_random_user_agent


@dataclass
class ScrapedContent:
    """Scraped website content."""

    about_text: str | None = None
    products: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    key_phrases: list[str] = field(default_factory=list)


class WebsiteScraper:
    """Scrape website for business intelligence."""

    # Pages to check for relevant content
    CONTENT_PATHS = [
        "/",
        "/about",
        "/about-us",
        "/products",
        "/services",
        "/what-we-do",
        "/our-story",
    ]

    # Common section identifiers
    ABOUT_SELECTORS = [
        "#about",
        ".about",
        "[class*='about']",
        "#mission",
        ".mission",
        "#story",
        ".story",
    ]

    PRODUCT_SELECTORS = [
        "#products",
        ".products",
        "[class*='product']",
        "#offerings",
        ".offerings",
    ]

    SERVICE_SELECTORS = [
        "#services",
        ".services",
        "[class*='service']",
    ]

    def __init__(self):
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers={
                "User-Agent": get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def scrape_website(self, url: str) -> ScrapedContent:
        """
        Scrape website for business content.

        Checks homepage and common content pages.
        """
        if not self.client:
            raise RuntimeError("Scraper not initialized. Use async with.")

        about_texts = []
        products = set()
        services = set()
        key_phrases = set()

        # Normalize URL
        if not url.startswith("http"):
            url = "https://" + url

        # Parse base URL
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Pages to check
        pages_to_check = [base_url]
        pages_to_check.extend(
            urljoin(base_url, path) for path in self.CONTENT_PATHS[1:]
        )

        # Check each page
        for page_url in pages_to_check:
            try:
                content = await self._scrape_page(page_url)
                if content.about_text:
                    about_texts.append(content.about_text)
                products.update(content.products)
                services.update(content.services)
                key_phrases.update(content.key_phrases)

                # Rate limit between pages
                await asyncio.sleep(0.5)

            except Exception:
                # Page might not exist or be inaccessible
                continue

        # Combine and deduplicate about text
        combined_about = " ".join(about_texts)
        if len(combined_about) > 1000:
            combined_about = combined_about[:1000] + "..."

        return ScrapedContent(
            about_text=combined_about if combined_about else None,
            products=list(products)[:20],  # Limit to 20 items
            services=list(services)[:20],
            key_phrases=list(key_phrases)[:15],
        )

    async def _scrape_page(self, url: str) -> ScrapedContent:
        """Scrape content from a single page."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = await self.client.get(url)

        if response.status_code != 200:
            return ScrapedContent()

        html = response.text
        soup = BeautifulSoup(html, "lxml")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Extract content
        about_text = self._extract_about(soup)
        products = self._extract_products(soup)
        services = self._extract_services(soup)
        key_phrases = self._extract_key_phrases(soup)

        return ScrapedContent(
            about_text=about_text,
            products=products,
            services=services,
            key_phrases=key_phrases,
        )

    def _extract_about(self, soup: BeautifulSoup) -> str | None:
        """Extract about/description text."""
        # Try specific about sections first
        for selector in self.ABOUT_SELECTORS:
            elements = soup.select(selector)
            for el in elements:
                text = el.get_text(strip=True, separator=" ")
                if len(text) > 50:  # Minimum meaningful content
                    return self._clean_text(text[:500])

        # Try meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return self._clean_text(meta_desc["content"])

        # Try first substantial paragraph
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 100:
                return self._clean_text(text[:500])

        return None

    def _extract_products(self, soup: BeautifulSoup) -> list[str]:
        """Extract product names/types."""
        products = set()

        # Check product sections
        for selector in self.PRODUCT_SELECTORS:
            elements = soup.select(selector)
            for el in elements:
                # Look for list items or headings
                for item in el.find_all(["li", "h3", "h4", "strong"]):
                    text = item.get_text(strip=True)
                    if 3 < len(text) < 100:
                        products.add(self._clean_text(text))

        # Look for product cards/items
        for el in soup.select("[class*='product-item'], [class*='product-card']"):
            title = el.find(["h2", "h3", "h4", "strong"])
            if title:
                text = title.get_text(strip=True)
                if 3 < len(text) < 100:
                    products.add(self._clean_text(text))

        return list(products)

    def _extract_services(self, soup: BeautifulSoup) -> list[str]:
        """Extract service offerings."""
        services = set()

        # Check service sections
        for selector in self.SERVICE_SELECTORS:
            elements = soup.select(selector)
            for el in elements:
                for item in el.find_all(["li", "h3", "h4", "strong"]):
                    text = item.get_text(strip=True)
                    if 3 < len(text) < 100:
                        services.add(self._clean_text(text))

        return list(services)

    def _extract_key_phrases(self, soup: BeautifulSoup) -> list[str]:
        """Extract key phrases and keywords."""
        phrases = set()

        # Get meta keywords
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords and meta_keywords.get("content"):
            for kw in meta_keywords["content"].split(","):
                kw = kw.strip()
                if 3 < len(kw) < 50:
                    phrases.add(kw.lower())

        # Look for emphasized text
        for el in soup.find_all(["strong", "em", "b"]):
            text = el.get_text(strip=True)
            if 3 < len(text) < 50:
                phrases.add(self._clean_text(text).lower())

        # Extract from headings
        for el in soup.find_all(["h1", "h2", "h3"]):
            text = el.get_text(strip=True)
            if 3 < len(text) < 80:
                phrases.add(self._clean_text(text).lower())

        return list(phrases)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r"[^\w\s.,!?-]", "", text)
        return text.strip()


async def scrape_company_website(url: str) -> ScrapedContent:
    """
    Convenience function to scrape a single company website.

    Args:
        url: Company website URL

    Returns:
        ScrapedContent with extracted information
    """
    async with WebsiteScraper() as scraper:
        return await scraper.scrape_website(url)


if __name__ == "__main__":
    # Test the scraper
    async def main():
        async with WebsiteScraper() as scraper:
            content = await scraper.scrape_website("https://organicvalley.coop")
            print(f"About: {content.about_text}")
            print(f"Products: {content.products}")
            print(f"Services: {content.services}")
            print(f"Key phrases: {content.key_phrases}")

    asyncio.run(main())
