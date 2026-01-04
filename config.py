"""Configuration for the food-finder lead generation tool."""

import random

# Database
DATABASE_URL = "sqlite:///leads.db"

# Rate limiting
MIN_DELAY_SECONDS = 2
MAX_DELAY_SECONDS = 5

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# USDA Organic Integrity Database API
USDA_ORGANIC_API_BASE = "https://organic.ams.usda.gov/integrity/api"

# Lead scoring weights
SCORING = {
    "employee_count_5_50": 20,
    "email_found": 15,
    "phone_found": 10,
    "no_crm_detected": 10,
    "has_job_postings": 10,
    "has_website": 5,
    "basic_website": 5,
}

# Disqualification thresholds
MAX_EMPLOYEE_COUNT = 50

# CRM detection patterns (in HTML source)
CRM_PATTERNS = [
    "hubspot",
    "salesforce",
    "sf.com",
    "pardot",
    "marketo",
    "zoho.com/crm",
]


def get_random_user_agent() -> str:
    """Return a random user agent for request rotation."""
    return random.choice(USER_AGENTS)


def get_random_delay() -> float:
    """Return a random delay for rate limiting."""
    return random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
