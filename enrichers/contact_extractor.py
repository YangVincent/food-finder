"""
Contact information extractor.

Scrapes websites to find email addresses and phone numbers.
"""

import asyncio
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from config import get_random_delay, get_random_user_agent


@dataclass
class ContactInfo:
    """Extracted contact information."""

    emails: list[str]
    phones: list[str]
    social_links: dict[str, str]  # platform -> url


class ContactExtractor:
    """Extract contact information from websites."""

    # Pages most likely to have contact info
    CONTACT_PATHS = [
        "/contact",
        "/contact-us",
        "/about",
        "/about-us",
        "/connect",
        "/reach-us",
    ]

    # Email pattern
    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE,
    )

    # Phone patterns (US)
    PHONE_PATTERNS = [
        re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"),
        re.compile(r"\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}"),
        re.compile(r"1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}"),
    ]

    # Emails to exclude (generic/spam traps)
    EXCLUDED_EMAILS = {
        "example@example.com",
        "test@test.com",
        "email@email.com",
        "info@example.com",
        "support@example.com",
        "noreply@",
        "no-reply@",
        "donotreply@",
    }

    def __init__(self):
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        # Use short timeouts to skip unresponsive/SSL-broken sites quickly
        # connect=5.0 catches SSL handshake issues, total timeout=10s
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
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

    async def extract_from_website(self, url: str) -> ContactInfo:
        """
        Extract contact information from a website.

        Checks the homepage and common contact pages.
        """
        if not self.client:
            raise RuntimeError("Extractor not initialized. Use async with.")

        emails = set()
        phones = set()
        social_links = {}

        # Normalize URL
        if not url.startswith("http"):
            url = "https://" + url

        # Parse base URL
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Pages to check
        pages_to_check = [url]  # Homepage
        pages_to_check.extend(
            urljoin(base_url, path) for path in self.CONTACT_PATHS
        )

        # Check each page
        for page_url in pages_to_check:
            try:
                page_info = await self._extract_from_page(page_url)
                emails.update(page_info.emails)
                phones.update(page_info.phones)
                social_links.update(page_info.social_links)

                # Rate limit between pages
                await asyncio.sleep(1)

            except Exception as e:
                # Page might not exist or be inaccessible
                continue

        return ContactInfo(
            emails=list(emails),
            phones=list(phones),
            social_links=social_links,
        )

    async def _extract_from_page(self, url: str) -> ContactInfo:
        """Extract contact info from a single page."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = await self.client.get(url)

        # Only process successful responses
        if response.status_code != 200:
            return ContactInfo(emails=[], phones=[], social_links={})

        html = response.text
        soup = BeautifulSoup(html, "lxml")

        # Extract emails
        emails = self._extract_emails(html, soup)

        # Extract phones
        phones = self._extract_phones(html)

        # Extract social links
        social_links = self._extract_social_links(soup)

        return ContactInfo(
            emails=emails,
            phones=phones,
            social_links=social_links,
        )

    def _extract_emails(self, html: str, soup: BeautifulSoup) -> list[str]:
        """Extract email addresses from HTML."""
        emails = set()

        # Find mailto links
        for link in soup.select('a[href^="mailto:"]'):
            href = link.get("href", "")
            email = href.replace("mailto:", "").split("?")[0].strip()
            if self._is_valid_email(email):
                emails.add(email.lower())

        # Find emails in text
        for match in self.EMAIL_PATTERN.finditer(html):
            email = match.group(0)
            if self._is_valid_email(email):
                emails.add(email.lower())

        return list(emails)

    def _is_valid_email(self, email: str) -> bool:
        """Check if email looks valid and not generic."""
        email = email.lower()

        # Check excluded patterns
        for excluded in self.EXCLUDED_EMAILS:
            if excluded in email:
                return False

        # Check for image file extensions (common false positives)
        if any(ext in email for ext in [".png", ".jpg", ".gif", ".svg"]):
            return False

        # Check for minimum length
        if len(email) < 6:
            return False

        return True

    def _extract_phones(self, html: str) -> list[str]:
        """Extract phone numbers from HTML."""
        phones = set()

        for pattern in self.PHONE_PATTERNS:
            for match in pattern.finditer(html):
                phone = match.group(0)
                # Normalize phone format
                normalized = self._normalize_phone(phone)
                if normalized:
                    phones.add(normalized)

        return list(phones)

    def _normalize_phone(self, phone: str) -> str | None:
        """Normalize phone number to consistent format."""
        # Remove all non-digits
        digits = re.sub(r"\D", "", phone)

        # US numbers should have 10 or 11 digits (with country code)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]  # Remove country code
        elif len(digits) != 10:
            return None

        # Format as (XXX) XXX-XXXX
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

    def _extract_social_links(self, soup: BeautifulSoup) -> dict[str, str]:
        """Extract social media links."""
        social_platforms = {
            "facebook": "facebook.com",
            "twitter": "twitter.com",
            "linkedin": "linkedin.com",
            "instagram": "instagram.com",
            "youtube": "youtube.com",
        }

        found = {}

        for link in soup.select("a[href]"):
            href = link.get("href", "").lower()
            for platform, domain in social_platforms.items():
                if domain in href and platform not in found:
                    found[platform] = link.get("href")

        return found


async def extract_contacts_for_companies(
    companies: list[dict],
) -> list[dict]:
    """
    Extract contact info for a list of companies with websites.

    Args:
        companies: List of dicts with 'website' key

    Returns:
        Same list with 'email', 'phone', 'social_links' keys added
    """
    async with ContactExtractor() as extractor:
        for company in companies:
            website = company.get("website")
            if not website:
                continue

            try:
                info = await extractor.extract_from_website(website)

                # Use first email/phone found
                company["email"] = info.emails[0] if info.emails else None
                company["phone"] = info.phones[0] if info.phones else None
                company["all_emails"] = info.emails
                company["all_phones"] = info.phones
                company["social_links"] = info.social_links

            except Exception as e:
                print(f"Error extracting contacts from {website}: {e}")

            # Rate limit
            await asyncio.sleep(get_random_delay())

    return companies


if __name__ == "__main__":
    # Test the extractor
    async def main():
        async with ContactExtractor() as extractor:
            # Test with a sample website
            info = await extractor.extract_from_website("https://organicvalley.coop")
            print(f"Emails: {info.emails}")
            print(f"Phones: {info.phones}")
            print(f"Social: {info.social_links}")

    asyncio.run(main())
