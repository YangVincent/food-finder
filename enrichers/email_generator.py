"""
AI-powered email generator for personalized outreach.

Uses Claude API to generate targeted emails based on company research.
"""

import json
from dataclasses import dataclass

import anthropic

from config import ANTHROPIC_API_KEY
from enrichers.website_scraper import ScrapedContent


@dataclass
class GeneratedEmail:
    """Generated email content."""

    subject: str
    body: str


# Our value proposition for the emails
VALUE_PROPOSITION = """
We help food and agriculture companies streamline their operations with:
- Document information extraction for sourcing new suppliers efficiently
- Upload and tracking of import/export documents
- Automated compliance documentation and reporting
"""


class EmailGenerator:
    """Generate personalized outreach emails using Claude."""

    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Please set the environment variable."
            )
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def generate_email(
        self,
        company_name: str,
        location: str | None,
        website: str | None,
        scraped_content: ScrapedContent | None,
    ) -> GeneratedEmail:
        """
        Generate a personalized outreach email.

        Args:
            company_name: Name of the company
            location: City, State of the company
            website: Company website URL
            scraped_content: Scraped information about the company

        Returns:
            GeneratedEmail with subject and body
        """
        prompt = self._build_prompt(company_name, location, website, scraped_content)

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract the response text
        response_text = message.content[0].text

        # Try to parse as JSON
        try:
            # Find JSON in the response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                return GeneratedEmail(
                    subject=data.get("subject", "Introduction"),
                    body=data.get("body", response_text),
                )
        except json.JSONDecodeError:
            pass

        # Fallback: use the whole response as body
        return GeneratedEmail(
            subject=f"Partnership Opportunity for {company_name}",
            body=response_text,
        )

    def _build_prompt(
        self,
        company_name: str,
        location: str | None,
        website: str | None,
        scraped_content: ScrapedContent | None,
    ) -> str:
        """Build the prompt for email generation."""
        # Build company context
        company_info = f"Company: {company_name}"
        if location:
            company_info += f"\nLocation: {location}"
        if website:
            company_info += f"\nWebsite: {website}"

        # Add scraped content if available
        scraped_info = ""
        if scraped_content:
            if scraped_content.about_text:
                scraped_info += f"\n\nAbout the company:\n{scraped_content.about_text}"
            if scraped_content.products:
                scraped_info += (
                    f"\n\nProducts they offer:\n- " + "\n- ".join(scraped_content.products[:10])
                )
            if scraped_content.services:
                scraped_info += (
                    f"\n\nServices they provide:\n- " + "\n- ".join(scraped_content.services[:10])
                )
            if scraped_content.key_phrases:
                scraped_info += (
                    f"\n\nKey business areas: {', '.join(scraped_content.key_phrases[:10])}"
                )

        prompt = f"""You are writing a personalized B2B outreach email for a document management SaaS product targeting food and agriculture companies.

{company_info}
{scraped_info}

Our value proposition:
{VALUE_PROPOSITION}

Write a personalized, professional cold outreach email that:
1. Opens with something specific about their business (from the company info above)
2. Identifies a relevant pain point they likely face with documentation or supplier management
3. Briefly explains how our solution addresses this
4. Ends with a clear, low-pressure call to action (like offering a brief call or demo)
5. Keeps a friendly but professional tone
6. Is concise - under 150 words for the body

Return your response as JSON with this exact format:
{{"subject": "Your subject line here", "body": "Your email body here"}}

Important: Only return the JSON, no other text."""

        return prompt


def generate_outreach_email(
    company_name: str,
    location: str | None = None,
    website: str | None = None,
    scraped_content: ScrapedContent | None = None,
) -> GeneratedEmail:
    """
    Convenience function to generate an outreach email.

    Args:
        company_name: Name of the target company
        location: Optional city, state
        website: Optional company website
        scraped_content: Optional scraped website content

    Returns:
        GeneratedEmail with subject and body
    """
    generator = EmailGenerator()
    return generator.generate_email(company_name, location, website, scraped_content)


if __name__ == "__main__":
    # Test the generator
    from enrichers.website_scraper import ScrapedContent

    test_content = ScrapedContent(
        about_text="Organic Valley is a farmer-owned cooperative producing organic dairy products since 1988.",
        products=["Organic Milk", "Cheese", "Butter", "Eggs"],
        services=["Farm partnerships", "Distribution"],
        key_phrases=["organic", "farmer-owned", "sustainable", "dairy"],
    )

    email = generate_outreach_email(
        company_name="Organic Valley",
        location="La Farge, WI",
        website="organicvalley.coop",
        scraped_content=test_content,
    )

    print(f"Subject: {email.subject}")
    print(f"\nBody:\n{email.body}")
