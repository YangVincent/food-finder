"""
Lead scoring logic.

Scores and qualifies leads based on available signals.
"""

from config import SCORING, MAX_EMPLOYEE_COUNT
from storage.models import Company


def score_lead(company: Company) -> tuple[float, bool, str | None]:
    """
    Score a lead and determine if it's qualified.

    Args:
        company: Company object to score

    Returns:
        Tuple of (score, is_qualified, disqualification_reason)
    """
    score = 0.0
    is_qualified = True
    disqualification_reason = None

    # Check employee count
    if company.employee_count:
        if 5 <= company.employee_count <= MAX_EMPLOYEE_COUNT:
            score += SCORING["employee_count_5_50"]
        elif company.employee_count > MAX_EMPLOYEE_COUNT:
            is_qualified = False
            disqualification_reason = f"Too large: {company.employee_count} employees"

    # Check contact info
    if company.email:
        score += SCORING["email_found"]
    if company.phone:
        score += SCORING["phone_found"]

    # Check for CRM (disqualify if found)
    if company.has_crm is True:
        is_qualified = False
        disqualification_reason = "Has CRM system"
    elif company.has_crm is False:
        score += SCORING["no_crm_detected"]

    # Check for job postings (growth signal)
    if company.has_job_postings:
        score += SCORING["has_job_postings"]

    # Check for website
    if company.website:
        score += SCORING["has_website"]

    # Check tech stack - basic website gets bonus
    tech_stack = company.tech_stack or ""
    if "SPA:" not in tech_stack:
        score += SCORING["basic_website"]

    return score, is_qualified, disqualification_reason


def score_company_dict(company: dict) -> dict:
    """
    Score a company from a dictionary (for enrichment pipeline).

    Args:
        company: Dict with company data

    Returns:
        Same dict with score, is_qualified, disqualification_reason added
    """
    score = 0.0
    is_qualified = True
    disqualification_reason = None

    # Check employee count
    employee_count = company.get("employee_count")
    if employee_count:
        if 5 <= employee_count <= MAX_EMPLOYEE_COUNT:
            score += SCORING["employee_count_5_50"]
        elif employee_count > MAX_EMPLOYEE_COUNT:
            is_qualified = False
            disqualification_reason = f"Too large: {employee_count} employees"

    # Check contact info
    if company.get("email"):
        score += SCORING["email_found"]
    if company.get("phone"):
        score += SCORING["phone_found"]

    # Check for CRM (disqualify if found)
    if company.get("has_crm") is True:
        is_qualified = False
        disqualification_reason = f"Has CRM: {company.get('crm_detected', 'unknown')}"
    elif company.get("has_crm") is False:
        score += SCORING["no_crm_detected"]

    # Check for website
    if company.get("website"):
        score += SCORING["has_website"]

    # Check tech stack - basic website gets bonus
    if not company.get("is_spa", False):
        score += SCORING["basic_website"]

    company["score"] = score
    company["is_qualified"] = is_qualified
    company["disqualification_reason"] = disqualification_reason

    return company


def get_score_breakdown(company: dict) -> list[str]:
    """
    Get a human-readable breakdown of a company's score.

    Args:
        company: Dict with company data

    Returns:
        List of scoring explanations
    """
    breakdown = []

    employee_count = company.get("employee_count")
    if employee_count:
        if 5 <= employee_count <= MAX_EMPLOYEE_COUNT:
            breakdown.append(f"+{SCORING['employee_count_5_50']}: {employee_count} employees (target range)")
        elif employee_count > MAX_EMPLOYEE_COUNT:
            breakdown.append(f"DISQUALIFIED: {employee_count} employees (too large)")

    if company.get("email"):
        breakdown.append(f"+{SCORING['email_found']}: Email found")
    if company.get("phone"):
        breakdown.append(f"+{SCORING['phone_found']}: Phone found")

    if company.get("has_crm") is True:
        breakdown.append(f"DISQUALIFIED: Has CRM ({company.get('crm_detected', 'unknown')})")
    elif company.get("has_crm") is False:
        breakdown.append(f"+{SCORING['no_crm_detected']}: No CRM detected")

    if company.get("website"):
        breakdown.append(f"+{SCORING['has_website']}: Has website")

    if not company.get("is_spa", False):
        breakdown.append(f"+{SCORING['basic_website']}: Basic website (no SPA)")

    total = company.get("score", 0)
    breakdown.append(f"TOTAL: {total}")

    return breakdown
