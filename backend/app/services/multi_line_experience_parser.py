"""
Multi-line experience and projects parser for handling resume formats where
work experience and projects are structured across multiple lines:

Format:
    Line 1: Company/Project Name [large gap] Location/Client
    Line 2: Designation/Title [large gap] Dates
    Line 3+: Bullet points with responsibilities/descriptions
"""

import re
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Date pattern and helpers
# ─────────────────────────────────────────────────────────────────────────────

DATE_PATTERN = re.compile(
    r"""
    (?:
        \b(?P<start_month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)
        [\s\-–—]*
        (?P<start_year>\d{4})\b
        (?:\s*[–—-]\s*
            (?:(?P<end_month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)
             [\s\-–—]*)?
            (?P<end_year>\d{4}|Present|Current)?\b
        )?
    )
    |
    (?:
        \b(?P<alt_start_year>\d{4})\s*[-–—]\s*(?P<alt_end_year>\d{4}|Present|Current)\b
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

LOCATION_INDICATORS = {
    "india", "usa", "uk", "canada", "australia", "germany", "france", "singapore",
    "bangalore", "pune", "mumbai", "delhi", "hyderabad", "chennai", "kolkata",
    "remote", "onsite", "hybrid", "work from home", "wfh"
}

BULLET_PATTERN = re.compile(r"^[\s•\-\*\→\►\–]*\s+")


def _extract_dates_from_line(line: str) -> Tuple[str, str]:
    """Extract start and end dates from a line.
    
    Returns:
        Tuple of (date_range_str, remaining_line_after_date)
    
    Example:
        Input:  "Lead Data Engineer - October 2023 - Present"
        Output: ("October 2023 - Present", "Lead Data Engineer")
    """
    date_match = DATE_PATTERN.search(line)
    if not date_match:
        return "", line
    
    date_str = date_match.group(0).strip()
    before = line[:date_match.start()].strip()
    after = line[date_match.end():].strip()
    
    # Clean up the "before" part by removing trailing separators
    # This handles cases like "Lead Data Engineer -" or "Lead Data Engineer –"
    before = re.sub(r'\s*[-–—]\s*$', '', before).strip()
    
    # Combine before and after, filtering out empty parts
    remaining_parts = [p for p in [before, after] if p]
    remaining = " ".join(remaining_parts).strip()
    
    return date_str, remaining


def _split_line_left_right(line: str) -> Tuple[str, str]:
    """Split a line into left and right parts using large whitespace gaps or patterns.
    
    Handles:
    - "Company Name                Location"
    - "Company Name    |    Location"
    - "Company Name - Location"
    
    Returns:
        Tuple of (left_part, right_part)
    """
    line = line.strip()
    
    # Try pipe separator first
    if " | " in line or "|" in line:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2:
            return parts[0], parts[1]
    
    # Try dash/em-dash separator (but not in company names)
    if " – " in line or " — " in line or " -– " in line:
        for sep in [" — ", " – ", " -– "]:
            if sep in line:
                parts = line.split(sep, 1)
                if len(parts) == 2:
                    return parts[0].strip(), parts[1].strip()
    
    # Try large whitespace (4+ spaces)
    large_space_match = re.search(r"(.+?)\s{4,}(.+)", line)
    if large_space_match:
        return large_space_match.group(1).strip(), large_space_match.group(2).strip()
    
    # No clear split - return as left only
    return line, ""


def _is_location(text: str) -> bool:
    """Check if text looks like a location."""
    if not text:
        return False
    lower = text.lower()
    # Check if any location indicator is in the text
    for indicator in LOCATION_INDICATORS:
        if indicator in lower:
            return True
    # Check for patterns like "City, Country" or "City, State"
    if re.match(r"^[A-Z][a-z]+\s*,\s*[A-Z]", text):
        return True
    return False


def _is_job_title(text: str) -> bool:
    """Check if text looks like a job title/designation."""
    if not text:
        return False
    
    job_keywords = {
        "engineer", "developer", "manager", "director", "lead", "senior",
        "analyst", "architect", "consultant", "specialist", "associate",
        "coordinator", "officer", "executive", "administrator", "designer",
        "scientist", "researcher", "intern", "trainee", "associate",
        "programmer", "specialist", "expert", "lead", "principal"
    }
    
    lower = text.lower()
    for keyword in job_keywords:
        if keyword in lower:
            return True
    return False


def _is_company_name(text: str) -> bool:
    """Check if text looks like a company name."""
    if not text or _is_location(text) or _is_job_title(text):
        return False
    
    # Known companies
    known_companies = {
        "ust", "ibm", "accenture", "tcs", "infosys", "wipro", "deloitte",
        "pwc", "capgemini", "cognizant", "mindtree", "synopsys", "qualcomm",
        "google", "microsoft", "amazon", "apple", "meta", "netflix", "adobe",
        "salesforce", "oracle", "sap", "bitwise", "vodafone", "hdfc", "icici"
    }
    
    # Company name is typically 2-5 words, starts with capital
    if re.match(r"^[A-Z]", text):
        lower = text.lower()
        if lower in known_companies:
            return True
        # Accepts alphanumeric company-like patterns
        if re.match(r"^[A-Z][A-Za-z0-9\s\-&.()]*$", text) and len(text) > 1:
            return True
    
    return False


def _is_role_and_dates_line(line: str) -> Tuple[bool, str, str]:
    """Check if a line contains role/title AND dates (but NOT a company name).
    
    This helps group role+date lines with company+location lines.
    
    Returns:
        Tuple of (is_role_dates: bool, role: str, dates: str)
    """
    line = line.strip()
    
    # Must NOT be a company name
    left, right = _split_line_left_right(line)
    if _is_company_name(left) or _is_company_name(right):
        return False, "", ""
    
    # Must contain date pattern
    date_str, remaining = _extract_dates_from_line(line)
    if not date_str:
        return False, "", ""
    
    # Remaining part should look like a job title
    if remaining and _is_job_title(remaining):
        return True, remaining, date_str
    
    # Alternative: check if left part is a job title when dates are on right
    if date_str and _is_job_title(left) and _is_location(right) == False:
        return True, left, date_str
    
    return False, "", ""


def _group_experience_lines(lines: List[str]) -> List[List[str]]:
    """Group lines that belong to the same experience entry.
    
    Detects when a line with (role + dates) follows a line with (company + location)
    and groups them together instead of treating them as separate entries.
    
    Returns:
        List of line groups, where each group is the lines for one experience
    """
    if not lines:
        return []
    
    groups: List[List[str]] = []
    current_group: List[str] = []
    i = 0
    
    while i < len(lines):
        line = (lines[i] or "").strip()
        i += 1
        
        # Skip empty lines
        if not line:
            if current_group:
                groups.append(current_group)
                current_group = []
            continue
        
        # Check if this is a company+location line
        left, right = _split_line_left_right(line)
        is_company_line = _is_company_name(left) and (not right or _is_location(right))
        
        if is_company_line:
            # Save previous group if any
            if current_group:
                groups.append(current_group)
            
            # Start new group with company+location line
            current_group = [line]
            
            # Look ahead: if next line is role+dates, add it to same group
            if i < len(lines):
                next_line = (lines[i] or "").strip()
                is_role_dates, _, _ = _is_role_and_dates_line(next_line)
                
                if is_role_dates:
                    # This role+dates line belongs with current company line
                    current_group.append(next_line)
                    i += 1  # Skip the role+dates line, it's now grouped
        else:
            # Not a company line - could be role+dates, bullet, or other
            current_group.append(line)
    
    if current_group:
        groups.append(current_group)
    
    return groups


# ─────────────────────────────────────────────────────────────────────────────
# Multi-line experience parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_experience_multiline(lines: List[str]) -> List[Dict]:
    """Parse work experience from multi-line format with intelligent grouping.
    
    Format:
        Line N: Company Name [gap] Location
        Line N+1: Designation [gap] Dates (e.g., October 2023 - Present)
        Line N+2+: Bullet points with responsibilities
    
    Uses intelligent grouping to detect when role+dates line follows company+location
    and groups them as a single experience entry.
    
    Args:
        lines: List of text lines from resume experience section
    
    Returns:
        List of dicts with keys: company, title, location, dates, responsibilities
    """
    # First, group lines that belong together
    line_groups = _group_experience_lines(lines)
    
    if not line_groups:
        return []
    
    experiences = []
    
    for group in line_groups:
        if not group:
            continue
        
        # Parse each group as an experience entry
        current_exp: Dict = {
            "company": "",
            "title": "",
            "location": "",
            "dates": "",
            "responsibilities": []
        }
        
        for i, line in enumerate(group):
            line = line.strip()
            if not line:
                continue
            
            # Skip bullet points for now (we'll collect them later)
            if BULLET_PATTERN.match(line):
                continue
            
            # First line should be company + location
            if i == 0:
                left, right = _split_line_left_right(line)
                if _is_company_name(left):
                    current_exp["company"] = left
                    if right and _is_location(right):
                        current_exp["location"] = right
                continue
            
            # Second line should be role/title + dates
            if i == 1 or (i > 1 and not current_exp["title"]):
                is_role_dates, role, dates = _is_role_and_dates_line(line)
                if is_role_dates:
                    current_exp["title"] = role
                    current_exp["dates"] = dates
                else:
                    # Try to extract even if not detected as role+dates
                    dates_str, remaining = _extract_dates_from_line(line)
                    if dates_str:
                        current_exp["dates"] = dates_str
                        # The remaining text after date removal is the designation/title
                        if remaining and remaining.strip():
                            current_exp["title"] = remaining.strip()
                        else:
                            # If remaining is empty, try splitting the original line
                            left, right = _split_line_left_right(line)
                            if _is_job_title(left):
                                current_exp["title"] = left
                            elif _is_job_title(right):
                                current_exp["title"] = right
                continue
        
        # Collect all responsibility bullet points from the group
        for line in group:
            line = line.strip()
            if BULLET_PATTERN.match(line):
                resp = BULLET_PATTERN.sub("", line).strip()
                if resp:
                    current_exp["responsibilities"].append(resp)
        
        # Add if has meaningful data
        if current_exp["company"] or current_exp["title"]:
            experiences.append(current_exp)
    
    return experiences


# ─────────────────────────────────────────────────────────────────────────────
# Multi-line projects parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_projects_multiline(lines: List[str]) -> List[Dict]:
    """Parse projects from multi-line format.
    
    Format:
        Line N: Project Name [gap] Client/Company
        Line N+1: Description/Role [gap] Dates (optional)
        Line N+2+: Bullet points with details/technologies
    
    Args:
        lines: List of text lines from resume projects section
    
    Returns:
        List of dicts with keys: name, description, client, role, dates, responsibilities, technologies
    """
    projects = []
    current_proj: Optional[Dict] = None
    i = 0
    
    while i < len(lines):
        line = (lines[i] or "").strip()
        i += 1
        
        # Skip empty lines
        if not line:
            continue
        
        # Skip if it's a bullet point (we're in details section)
        if BULLET_PATTERN.match(line):
            if current_proj:
                detail = BULLET_PATTERN.sub("", line).strip()
                if detail:
                    # Check if it's a technology or responsibility
                    if any(tech in detail.lower() for tech in ["javascript", "python", "java", "c#", "sql", "html", "css", "react", "angular", "node", "docker", "kubernetes", "aws", "azure"]):
                        current_proj["technologies"].append(detail)
                    else:
                        current_proj["responsibilities"].append(detail)
            continue
        
        # Check if this looks like a project name line
        left, right = _split_line_left_right(line)
        
        # Heuristic: if left part is short and capitalized, it's probably the project name
        if left and len(left) < 60 and re.match(r"^[A-Z]", left):
            # Save previous project if any
            if current_proj and current_proj.get("name"):
                projects.append(current_proj)
            
            # Start new project entry
            current_proj = {
                "name": left,
                "description": "",
                "client": right if right and not _is_job_title(right) else "",
                "role": "",
                "dates": "",
                "responsibilities": [],
                "technologies": []
            }
            
            # Look ahead for description/role line
            if i < len(lines):
                next_line = (lines[i] or "").strip()
                if next_line and not BULLET_PATTERN.match(next_line):
                    dates_str, remaining = _extract_dates_from_line(next_line)
                    current_proj["dates"] = dates_str
                    
                    if remaining:
                        left_part, right_part = _split_line_left_right(remaining)
                        # Check which part contains role/description
                        if _is_job_title(left_part):
                            current_proj["role"] = left_part
                            if right_part:
                                current_proj["description"] = right_part
                        elif _is_job_title(right_part):
                            current_proj["role"] = right_part
                            if left_part:
                                current_proj["description"] = left_part
                        else:
                            # Neither is clearly a role, use as description
                            current_proj["description"] = (left_part + " " + right_part).strip()
                    
                    i += 1
    
    if current_proj and current_proj.get("name"):
        projects.append(current_proj)
    
    return projects


# ─────────────────────────────────────────────────────────────────────────────
# Validation and enhancement
# ─────────────────────────────────────────────────────────────────────────────

def validate_and_enhance_experience(experiences: List[Dict]) -> List[Dict]:
    """Validate and enhance parsed experience entries.
    
    Args:
        experiences: List of experience dicts from parser
    
    Returns:
        Enhanced list with corrected fields
    """
    for exp in experiences:
        # Clean empty strings
        for key in exp:
            if isinstance(exp[key], str):
                exp[key] = exp[key].strip()
        
        # Validate company/title/location
        company = exp.get("company", "").strip()
        title = exp.get("title", "").strip()
        location = exp.get("location", "").strip()
        
        # If location looks like company, swap
        if location and _is_company_name(location) and not _is_company_name(company):
            exp["company"] = location
            exp["location"] = ""
        
        # If title looks like location, move it
        if title and _is_location(title) and not location:
            exp["location"] = title
            exp["title"] = ""
    
    return [e for e in experiences if e.get("company") or e.get("title")]


def validate_and_enhance_projects(projects: List[Dict]) -> List[Dict]:
    """Validate and enhance parsed project entries.
    
    Args:
        projects: List of project dicts from parser
    
    Returns:
        Enhanced list with corrected fields
    """
    for proj in projects:
        # Clean empty strings
        for key in proj:
            if isinstance(proj[key], str):
                proj[key] = proj[key].strip()
            elif isinstance(proj[key], list):
                proj[key] = [item.strip() for item in proj[key] if isinstance(item, str) and item.strip()]
        
        # Validate and cross-check fields
        name = proj.get("name", "").strip()
        client = proj.get("client", "").strip()
        role = proj.get("role", "").strip()
        
        # If client looks like a company but name doesn't, they might be swapped
        if client and _is_company_name(client) and name and not _is_company_name(name):
            # Keep as is, client is likely correct
            pass
    
    return [p for p in projects if p.get("name")]
