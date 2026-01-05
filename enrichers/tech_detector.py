"""
Technology stack detector.

Analyzes websites to detect CRM systems and other technologies.
Used to disqualify companies that already have sophisticated tooling.
"""

import asyncio
import re
from dataclasses import dataclass

import httpx

from config import get_random_user_agent, CRM_PATTERNS


@dataclass
class TechProfile:
    """Detected technology profile for a company."""

    has_crm: bool
    crm_detected: str | None  # Name of CRM if detected
    is_spa: bool  # Single page app (React/Angular/Vue)
    has_analytics: bool
    detected_tech: list[str]  # All detected technologies


class TechDetector:
    """Detect technologies used by a website."""

    # CRM patterns to look for in HTML/JS
    CRM_SIGNATURES = {
        "hubspot": [
            "js.hs-scripts.com",
            "js.hsforms.net",
            "hubspot.com",
            "_hsq",
            "hs-banner",
        ],
        "salesforce": [
            "force.com",
            "salesforce.com",
            "pardot.com",
            "sfdc",
            "lightning.force",
        ],
        "zoho": [
            "zoho.com/crm",
            "zohocrmsync",
            "zoho.salesiq",
        ],
        "pipedrive": [
            "pipedrive.com",
            "pd-track",
        ],
        "freshsales": [
            "freshsales.io",
            "freshworks.com",
        ],
        "marketo": [
            "marketo.com",
            "munchkin.js",
            "marketo.net",
        ],
        "intercom": [
            "intercom.io",
            "intercomcdn.com",
            "intercom-launcher",
        ],
    }

    # SPA framework signatures
    SPA_SIGNATURES = {
        "react": ["react", "__REACT", "reactroot", "_reactRoot"],
        "angular": ["ng-app", "ng-controller", "angular.js", "angular.min.js"],
        "vue": ["__vue__", "vue.js", "vue.min.js", "v-cloak"],
    }

    # Analytics signatures
    ANALYTICS_SIGNATURES = [
        "google-analytics.com",
        "googletagmanager.com",
        "analytics.js",
        "gtag",
        "mixpanel.com",
        "segment.com",
        "amplitude.com",
    ]

    def __init__(self):
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        # Use short timeouts to skip unresponsive/SSL-broken sites quickly
        # connect=5.0 catches SSL handshake issues, total timeout=10s
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=True,
            headers={"User-Agent": get_random_user_agent()},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def analyze_website(self, url: str) -> TechProfile:
        """
        Analyze a website's technology stack.

        Focuses on detecting CRM systems and SPAs.
        """
        if not self.client:
            raise RuntimeError("Detector not initialized. Use async with.")

        # Normalize URL
        if not url.startswith("http"):
            url = "https://" + url

        try:
            response = await self.client.get(url)
            if response.status_code != 200:
                return TechProfile(
                    has_crm=False,
                    crm_detected=None,
                    is_spa=False,
                    has_analytics=False,
                    detected_tech=[],
                )

            html = response.text.lower()
            return self._analyze_html(html)

        except Exception as e:
            print(f"Error analyzing {url}: {e}")
            return TechProfile(
                has_crm=False,
                crm_detected=None,
                is_spa=False,
                has_analytics=False,
                detected_tech=[],
            )

    def _analyze_html(self, html: str) -> TechProfile:
        """Analyze HTML source for technology signatures."""
        detected_tech = []
        crm_detected = None
        has_crm = False
        is_spa = False
        has_analytics = False

        # Check for CRM systems
        for crm_name, signatures in self.CRM_SIGNATURES.items():
            for sig in signatures:
                if sig.lower() in html:
                    has_crm = True
                    crm_detected = crm_name
                    detected_tech.append(f"CRM: {crm_name}")
                    break
            if has_crm:
                break

        # Check for SPA frameworks
        for framework, signatures in self.SPA_SIGNATURES.items():
            for sig in signatures:
                if sig.lower() in html:
                    is_spa = True
                    detected_tech.append(f"SPA: {framework}")
                    break

        # Check for analytics
        for sig in self.ANALYTICS_SIGNATURES:
            if sig.lower() in html:
                has_analytics = True
                detected_tech.append("Analytics detected")
                break

        return TechProfile(
            has_crm=has_crm,
            crm_detected=crm_detected,
            is_spa=is_spa,
            has_analytics=has_analytics,
            detected_tech=detected_tech,
        )


async def detect_tech_for_companies(companies: list[dict]) -> list[dict]:
    """
    Detect technology for a list of companies with websites.

    Args:
        companies: List of dicts with 'website' key

    Returns:
        Same list with 'has_crm', 'tech_stack' keys added
    """
    async with TechDetector() as detector:
        for company in companies:
            website = company.get("website")
            if not website:
                continue

            try:
                profile = await detector.analyze_website(website)
                company["has_crm"] = profile.has_crm
                company["crm_detected"] = profile.crm_detected
                company["is_spa"] = profile.is_spa
                company["tech_stack"] = profile.detected_tech

            except Exception as e:
                print(f"Error detecting tech for {website}: {e}")

            # Rate limit
            await asyncio.sleep(1)

    return companies


if __name__ == "__main__":
    # Test the detector
    async def main():
        async with TechDetector() as detector:
            # Test with sample websites
            for url in [
                "https://organicvalley.coop",
                "https://hubspot.com",  # Should detect HubSpot
            ]:
                profile = await detector.analyze_website(url)
                print(f"\n{url}")
                print(f"  Has CRM: {profile.has_crm} ({profile.crm_detected})")
                print(f"  Is SPA: {profile.is_spa}")
                print(f"  Tech: {profile.detected_tech}")

    asyncio.run(main())
