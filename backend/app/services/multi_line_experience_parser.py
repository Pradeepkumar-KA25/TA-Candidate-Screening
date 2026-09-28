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
    """Parse projects without promoting arbitrary prose to project entries."""
    projects: List[Dict] = []
    current: Optional[Dict] = None
    field_pattern = re.compile(
        r"^(?:project\s+)?(name|title|client|customer|role|duration|period|dates?"
        r"|technologies?|tech\s*stack|tools?|environment|description"
        r"|responsibilities|roles\s+and\s+responsibilities)\s*[:\-]\s*(.*)$",
        re.IGNORECASE,
    )
    numbered_project_pattern = re.compile(
        r"^project\s*(?:name\s*)?(?:[ivx]+|\d+)?\s*[:\-]\s*(.+)$",
        re.IGNORECASE,
    )
    project_heading_pattern = re.compile(
        r"^project\s*(?:[ivx]+|\d+)\s*[:\-]?$",
        re.IGNORECASE,
    )
    expecting_name = False

    def new_project(name: str) -> Dict:
        return {
            "name": name.strip(),
            "description": "",
            "client": "",
            "role": "",
            "dates": "",
            "responsibilities": [],
            "technologies": [],
        }

    def flush() -> None:
        nonlocal current
        if current and current.get("name"):
            projects.append(current)
        current = None

    def next_meaningful(index: int) -> str:
        for candidate in lines[index:]:
            text = str(candidate or "").strip()
            if text:
                return text
        return ""

    for index, raw_line in enumerate(lines):
        line = str(raw_line or "").strip()
        if not line:
            continue

        if project_heading_pattern.match(line):
            flush()
            expecting_name = True
            continue

        if expecting_name:
            current = new_project(line)
            expecting_name = False
            continue

        numbered_match = numbered_project_pattern.match(line)
        field_match = field_pattern.match(line)
        if numbered_match:
            flush()
            current = new_project(numbered_match.group(1))
            continue

        if field_match and field_match.group(1).lower() in {"name", "title"}:
            flush()
            current = new_project(field_match.group(2))
            continue

        if current is None:
            following = next_meaningful(index + 1)
            first_title = not projects and len(line.split()) <= 12 and not line.endswith((".", ";"))
            if len(line) <= 100 and (
                first_title or field_pattern.match(following) or BULLET_PATTERN.match(following)
            ):
                current = new_project(line)
            continue

        if field_match:
            label = field_match.group(1).lower()
            value = field_match.group(2).strip()
            if label in {"client", "customer"}:
                current["client"] = value
            elif label in {"role"}:
                current["role"] = value
            elif label in {"duration", "period", "date", "dates"}:
                current["dates"] = value
            elif label in {"technology", "technologies", "tech stack", "tool", "tools", "environment"}:
                current["technologies"].extend(
                    item.strip() for item in re.split(r"[,|;/]", value) if item.strip()
                )
            elif label in {"responsibilities", "roles and responsibilities"}:
                if value:
                    current["responsibilities"].append(value)
            elif label == "description" and value:
                current["description"] = (current["description"] + " " + value).strip()
            continue

        if BULLET_PATTERN.match(line):
            detail = BULLET_PATTERN.sub("", line).strip()
            if detail:
                current["responsibilities"].append(detail)
            continue

        dates, remaining = _extract_dates_from_line(line)
        if dates and not current["dates"]:
            current["dates"] = dates
            if remaining and _is_job_title(remaining) and not current["role"]:
                current["role"] = remaining
            elif remaining:
                current["description"] = (current["description"] + " " + remaining).strip()
            continue

        following = next_meaningful(index + 1)
        if field_pattern.match(following) and len(line) <= 100:
            flush()
            current = new_project(line)
        else:
            current["description"] = (current["description"] + " " + line).strip()

    flush()
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
