"""
Company type classifier.

Classifies companies by type based on:
- Domain patterns (.edu, .gov, .org)
- Company name keywords
- LinkedIn presence
- Website characteristics
"""

import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse


class CompanyType(str, Enum):
    """Types of companies we can classify."""
    RESEARCH_INSTITUTION = "research_institution"  # Universities, labs, research orgs
    GOVERNMENT = "government"  # Government agencies
    LARGE_COMPANY = "large_company"  # Enterprise, major brands
    ESTABLISHED_BUSINESS = "established_business"  # Mid-sized with LinkedIn, professional presence
    FARM = "farm"  # Agricultural producers - farms, ranches, orchards
    ARTISAN_SHOP = "artisan_shop"  # Small local shops - bakeries, cafes, roasters
    UNKNOWN = "unknown"


@dataclass
class CompanyClassification:
    """Classification result for a company."""
    company_type: CompanyType
    confidence: float  # 0-1 confidence in classification
    signals: list[str]  # Reasons for classification
    has_linkedin: bool
    is_edu: bool
    is_gov: bool


class CompanyClassifier:
    """Classify companies by type using available signals."""

    # Keywords indicating research institutions
    RESEARCH_KEYWORDS = {
        "university", "college", "institute", "laboratory", "lab",
        "research", "foundation", "association", "society", "academy",
        "school of", "department of", "center for", "centre for",
    }

    # Keywords indicating government
    GOVERNMENT_KEYWORDS = {
        "department of", "agency", "bureau", "federal", "state of",
        "county of", "city of", "municipal", "public", "authority",
    }

    # Keywords indicating farms/agricultural producers
    FARM_KEYWORDS = {
        "farm", "farms", "ranch", "ranches", "orchard", "orchards",
        "vineyard", "vineyards", "grove", "groves", "plantation",
        "acres", "acre", "agricultural", "grower", "growers",
        "produce", "harvest", "organic farm", "homestead",
    }

    # Keywords indicating artisan/small shops (retail/food service)
    ARTISAN_KEYWORDS = {
        "bakery", "kitchen", "cafe", "coffee", "roasters", "roastery",
        "creamery", "dairy", "apiary", "apiaries", "honey",
        "artisan", "handmade", "homemade", "craft", "small batch",
        "garden", "gardens", "greenhouse", "market",
    }

    # Keywords indicating larger/formal businesses
    ENTERPRISE_KEYWORDS = {
        "inc", "incorporated", "corp", "corporation", "llc", "ltd",
        "limited", "company", "co", "enterprises", "group", "holdings",
        "international", "global", "worldwide", "national",
        "distributors", "distribution", "logistics", "supply",
    }

    def __init__(self):
        pass

    def classify(
        self,
        name: str,
        website: str | None = None,
        linkedin_url: str | None = None,
        has_crm: bool | None = None,
        tech_stack: str | None = None,
        employee_count: int | None = None,
    ) -> CompanyClassification:
        """
        Classify a company based on available signals.

        Args:
            name: Company name
            website: Company website URL
            linkedin_url: LinkedIn company page URL
            has_crm: Whether CRM was detected
            tech_stack: Detected technologies
            employee_count: Number of employees if known

        Returns:
            CompanyClassification with type, confidence, and signals
        """
        signals = []
        scores = {t: 0.0 for t in CompanyType}

        name_lower = name.lower()
        has_linkedin = bool(linkedin_url)

        # Check domain patterns
        is_edu = False
        is_gov = False
        if website:
            try:
                parsed = urlparse(website if website.startswith("http") else f"https://{website}")
                domain = parsed.netloc.lower()
                if domain.startswith("www."):
                    domain = domain[4:]

                if domain.endswith(".edu") or ".edu." in domain:
                    is_edu = True
                    scores[CompanyType.RESEARCH_INSTITUTION] += 50
                    signals.append("Educational domain (.edu)")

                if domain.endswith(".gov") or ".gov." in domain:
                    is_gov = True
                    scores[CompanyType.GOVERNMENT] += 50
                    signals.append("Government domain (.gov)")

                if domain.endswith(".org"):
                    scores[CompanyType.RESEARCH_INSTITUTION] += 10
                    signals.append("Non-profit domain (.org)")

            except Exception:
                pass

        # Check name for research keywords
        for keyword in self.RESEARCH_KEYWORDS:
            if keyword in name_lower:
                scores[CompanyType.RESEARCH_INSTITUTION] += 20
                signals.append(f"Research keyword: '{keyword}'")
                break

        # Check name for government keywords
        for keyword in self.GOVERNMENT_KEYWORDS:
            if keyword in name_lower:
                scores[CompanyType.GOVERNMENT] += 20
                signals.append(f"Government keyword: '{keyword}'")
                break

        # Check name for farm keywords
        farm_score = 0
        for keyword in self.FARM_KEYWORDS:
            if keyword in name_lower:
                farm_score += 20
                signals.append(f"Farm keyword: '{keyword}'")
        scores[CompanyType.FARM] += farm_score

        # Check name for artisan keywords
        artisan_score = 0
        for keyword in self.ARTISAN_KEYWORDS:
            if keyword in name_lower:
                artisan_score += 15
                signals.append(f"Artisan keyword: '{keyword}'")
        scores[CompanyType.ARTISAN_SHOP] += artisan_score

        # Check name for enterprise keywords
        enterprise_score = 0
        for keyword in self.ENTERPRISE_KEYWORDS:
            if keyword in name_lower:
                enterprise_score += 10
                signals.append(f"Enterprise keyword: '{keyword}'")
        scores[CompanyType.LARGE_COMPANY] += enterprise_score
        scores[CompanyType.ESTABLISHED_BUSINESS] += enterprise_score * 0.5

        # LinkedIn presence indicates established business
        if has_linkedin:
            scores[CompanyType.ESTABLISHED_BUSINESS] += 25
            scores[CompanyType.LARGE_COMPANY] += 15
            signals.append("Has LinkedIn company page")
        else:
            scores[CompanyType.ARTISAN_SHOP] += 10
            scores[CompanyType.FARM] += 10
            signals.append("No LinkedIn company page")

        # CRM indicates larger/sophisticated operation
        if has_crm:
            scores[CompanyType.LARGE_COMPANY] += 30
            signals.append("Has CRM system")

        # Tech stack complexity
        if tech_stack:
            tech_lower = tech_stack.lower()
            if "spa:" in tech_lower:
                scores[CompanyType.ESTABLISHED_BUSINESS] += 10
                scores[CompanyType.LARGE_COMPANY] += 10
                signals.append("Modern web framework (SPA)")
            if "analytics" in tech_lower:
                scores[CompanyType.ESTABLISHED_BUSINESS] += 5
                signals.append("Has analytics")

        # Employee count
        if employee_count:
            if employee_count <= 5:
                scores[CompanyType.ARTISAN_SHOP] += 20
                scores[CompanyType.FARM] += 20
                signals.append(f"Small team ({employee_count} employees)")
            elif employee_count <= 50:
                scores[CompanyType.ESTABLISHED_BUSINESS] += 20
                scores[CompanyType.FARM] += 10  # Farms can be mid-sized too
                signals.append(f"Mid-sized team ({employee_count} employees)")
            else:
                scores[CompanyType.LARGE_COMPANY] += 30
                signals.append(f"Large team ({employee_count} employees)")

        # Default: if no strong signals, lean toward established business
        if max(scores.values()) < 15:
            scores[CompanyType.UNKNOWN] = 10

        # Find the winning type
        best_type = max(scores, key=lambda t: scores[t])
        best_score = scores[best_type]

        # Calculate confidence (normalize to 0-1)
        total_score = sum(scores.values())
        confidence = best_score / max(total_score, 1)

        return CompanyClassification(
            company_type=best_type,
            confidence=round(confidence, 2),
            signals=signals,
            has_linkedin=has_linkedin,
            is_edu=is_edu,
            is_gov=is_gov,
        )


def classify_company(company: dict) -> dict:
    """
    Classify a company from a dictionary.

    Args:
        company: Dict with company data

    Returns:
        Same dict with company_type, has_linkedin added
    """
    classifier = CompanyClassifier()
    result = classifier.classify(
        name=company.get("name", ""),
        website=company.get("website"),
        linkedin_url=company.get("linkedin_url"),
        has_crm=company.get("has_crm"),
        tech_stack=company.get("tech_stack"),
        employee_count=company.get("employee_count"),
    )

    company["company_type"] = result.company_type.value
    company["has_linkedin"] = result.has_linkedin
    company["classification_signals"] = result.signals

    return company


if __name__ == "__main__":
    # Test the classifier
    classifier = CompanyClassifier()

    test_cases = [
        {"name": "Vivio's Artisan GF Bakery", "website": "viviosartisangf.com"},
        {"name": "UC Davis Agricultural Sustainability Institute", "website": "asi.ucdavis.edu"},
        {"name": "Welch's", "website": "welchs.com", "has_crm": True},
        {"name": "Happy Valley Farm", "website": None},
        {"name": "Blue Bottle Coffee", "website": "bluebottlecoffee.com", "linkedin_url": "linkedin.com/company/blue-bottle"},
        {"name": "Organic Valley Cooperative", "website": "organicvalley.coop"},
    ]

    for company in test_cases:
        result = classifier.classify(
            name=company["name"],
            website=company.get("website"),
            linkedin_url=company.get("linkedin_url"),
            has_crm=company.get("has_crm"),
        )
        print(f"\n{company['name']}")
        print(f"  Type: {result.company_type.value}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Signals: {result.signals}")
