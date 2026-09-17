"""
Enhanced experience extraction with better company/location/designation parsing.

This module provides validation and correction logic to improve the parsing of
work experience entries from resumes, particularly for formats where:
- Company name and location appear together (e.g., "UST Pune, India")
- Job titles and company names might be misidentified
- Multiple entities need to be extracted from a single line
"""

import re
from typing import Dict, Optional, Tuple


# Common India cities and locations
INDIA_CITIES = {
    "bangalore", "bengaluru", "pune", "mumbai", "delhi", "new delhi",
    "hyderabad", "kolkata", "Chennai", "Ahmedabad", "Jaipur", "Surat",
    "Lucknow", "Indore", "Kochi", "Gurgaon", "Noida", "Chandigarh",
    "Visakhapatnam", "Nagpur", "Bhopal", "Vadodara", "Guwahati",
    "bangalore rural", "rajarhat", "whitefield", "indiranagar",
}

# Common company name patterns and known tech companies
KNOWN_COMPANIES = {
    "ust", "ibm", "accenture", "tcs", "infosys", "wipro", "cognizant",
    "capgemini", "deloitte", "kpmg", "pwc", "hsbc", "citibank", "amazon",
    "microsoft", "google", "apple", "oracle", "salesforce", "adobe",
    "vmware", "redhat", "datadog", "stripe", "uber", "airbnb",
    "bitwise", "kanini", "optum", "anthem", "aetna", "united health",
}

# Job role indicators
JOB_ROLE_KEYWORDS = {
    "engineer", "developer", "manager", "analyst", "architect", "designer",
    "consultant", "lead", "senior", "junior", "director", "head", "chief",
    "officer", "programmer", "specialist", "associate", "coordinator",
    "intern", "trainee", "executive", "administrator", "scientist",
    "data scientist", "ml engineer", "devops", "qa", "tester",
}

# Location indicators
LOCATION_KEYWORDS = {
    "india", "usa", "uk", "australia", "canada", "singapore", "dubai",
    "london", "new york", "san francisco", "new jersey", "california",
    "texas", "florida", "remote", "hybrid", "onsite",
}


def _is_location_pattern(text: str) -> bool:
    """Check if text matches location pattern (City, Country or City)."""
    if not text:
        return False
    
    # Pattern: City, Country or City, State
    if re.search(r'^\w+,\s*\w+', text):
        return True
    
    # Check for known cities
    text_lower = text.lower()
    for city in INDIA_CITIES:
        if city in text_lower:
            return True
    
    # Check for location keywords
    for keyword in LOCATION_KEYWORDS:
        if keyword in text_lower:
            return True
    
    return False


def _is_job_role(text: str) -> bool:
    """Check if text looks like a job title/role."""
    if not text:
        return False
    
    text_lower = text.lower()
    for keyword in JOB_ROLE_KEYWORDS:
        if keyword in text_lower:
            return True
    
    return False


def _is_company_name(text: str) -> bool:
    """Check if text looks like a company name."""
    if not text or len(text) > 100:
        return False
    
    text_lower = text.lower()
    
    # Known company check
    for company in KNOWN_COMPANIES:
        if company in text_lower:
            return True
    
    # Heuristics for company names:
    # - Short name (2-50 chars)
    # - Contains alphanumerics and maybe hyphens/spaces
    # - Doesn't look like a job role
    # - Doesn't look like a location
    if len(text) > 50 or len(text) < 2:
        return False
    
    if _is_location_pattern(text):
        return False
    
    if _is_job_role(text):
        return False
    
    # Should look like an organization name
    if re.match(r'^[A-Za-z0-9\s\-\.&]+$', text):
        return True
    
    return False


def _split_company_location(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Split a combined company+location string into separate parts.
    
    Examples:
    - "UST Pune, India" -> ("UST", "Pune, India")
    - "IBM" -> ("IBM", None)
    - "Pune, India" -> (None, "Pune, India")
    """
    if not text:
        return None, None
    
    # Pattern: word(s) followed by comma-separated location
    # E.g., "UST Pune, India" or "Company City, Country"
    match = re.match(r'^([^,]+?)\s+([^,]+,\s*.+)$', text.strip())
    if match:
        potential_company = match.group(1).strip()
        potential_location = match.group(2).strip()
        
        # Validate extraction
        if _is_location_pattern(potential_location):
            if not _is_location_pattern(potential_company):
                return potential_company, potential_location
    
    # Pattern: "Location, Location" - all location, no company
    if _is_location_pattern(text):
        return None, text
    
    # Pattern: Just company name
    if _is_company_name(text):
        return text, None
    
    # Fallback: assume it's a company if it doesn't look like location
    if not _is_location_pattern(text):
        return text, None
    
    return None, text


def validate_and_correct_experience(
    experience: Dict
) -> Dict:
    """
    Validate and correct parsed experience entry.
    
    Fixes common issues:
    - Company and location swapped
    - Location misidentified as company
    - Job role misidentified as company
    
    Args:
        experience: Dict with keys 'title', 'company', 'location', 'dates', 'responsibilities'
    
    Returns:
        Corrected experience dict
    """
    if not experience:
        return experience
    
    title = experience.get("title", "").strip()
    company = experience.get("company", "").strip()
    location = experience.get("location", "").strip()
    
    # Try to split company+location if both are in company field
    if company and not location:
        potential_company, potential_location = _split_company_location(company)
        if potential_company and potential_location:
            company = potential_company
            location = potential_location
        elif not potential_company and potential_location:
            location = potential_location
            company = ""
            # If title looks like a company and company field had only location
            if title and _is_company_name(title) and not _is_location_pattern(title):
                company = title
                title = ""
    
    # Fix swaps: if company looks like location and location looks like company
    if company and _is_location_pattern(company) and location and _is_company_name(location):
        company, location = location, company
    
    # Fix: location assigned to company field, try to use title as company
    if company and _is_location_pattern(company) and not location:
        location = company
        # If title looks like a company, use it as company
        if title and _is_company_name(title):
            company = title
            title = ""
        else:
            company = ""
    
    # Fix: job role assigned to company field, but title field has company
    if company and _is_job_role(company) and title and _is_company_name(title):
        company, title = title, company
    
    # Fix: location assigned to title field
    if title and _is_location_pattern(title) and not location and company:
        location = title
        title = ""
    
    # Ensure company and title aren't the same
    if title and company and title.lower() == company.lower():
        if _is_job_role(title):
            company = ""
        elif _is_company_name(company):
            title = ""
    
    # Update the experience dict
    result = experience.copy()
    result["title"] = title
    result["company"] = company
    result["location"] = location
    
    return result


def enhance_experience_list(experiences: list) -> list:
    """
    Apply corrections to a list of experience entries.
    
    Args:
        experiences: List of experience dicts
    
    Returns:
        List of corrected experience dicts
    """
    return [validate_and_correct_experience(exp) for exp in experiences if exp]
