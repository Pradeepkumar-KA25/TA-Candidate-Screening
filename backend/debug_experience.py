#!/usr/bin/env python3
"""Debug script to trace experience correction flow."""
import sys
sys.path.insert(0, '.')

from app.services.experience_extraction_enhancer import (
    _is_location_pattern,
    _is_company_name,
    _is_job_role,
)

def debug_validate_and_correct_experience(experience):
    """Debug version with print statements."""
    print("=== Starting validation ===")
    
    if not experience:
        return experience
    
    title = experience.get("title", "").strip()
    company = experience.get("company", "").strip()
    location = experience.get("location", "").strip()
    
    print(f"Initial state:")
    print(f"  title='{title}'")
    print(f"  company='{company}'")
    print(f"  location='{location}'")
    
    # Step 1: Try to split company+location if both are in company field
    if company and not location:
        print(f"\nStep 1: Check if company+location combined...")
        print(f"  company is not empty: {bool(company)}, location is empty: {not location}")
        # We're not splitting here, so skip this step
    
    # Step 2: Fix swaps: if company looks like location and location looks like company
    if company and _is_location_pattern(company) and location and _is_company_name(location):
        print(f"\nStep 2: Swap company/location...")
        company, location = location, company
        print(f"  After swap: company='{company}', location='{location}'")
    
    # Step 3: Fix: location assigned to company field, try to use title as company
    if company and _is_location_pattern(company) and not location:
        print(f"\nStep 3: Location in company field...")
        print(f"  company is location pattern: {_is_location_pattern(company)}")
        print(f"  location is empty: {not location}")
        location = company
        print(f"  Moved company to location: location='{location}'")
        
        # If title looks like a company, use it as company
        print(f"  Check if title '{title}' is company: {_is_company_name(title)}")
        if title and _is_company_name(title):
            print(f"  Yes! Setting company='{title}', title=''")
            company = title
            title = ""
        else:
            print(f"  No. Clearing company")
            company = ""
    
    print(f"\nFinal state:")
    print(f"  title='{title}'")
    print(f"  company='{company}'")
    print(f"  location='{location}'")
    
    result = experience.copy()
    result["title"] = title
    result["company"] = company
    result["location"] = location
    
    return result

# Test case
exp = {
    "company": "Pune, India",
    "title": "UST",
    "location": "",
    "dates": "October 2023 – Present",
    "responsibilities": [],
}

result = debug_validate_and_correct_experience(exp)
print("\n" + "="*50)
print("Expected: company='UST', location='Pune, India'")
print(f"Got: company='{result['company']}', location='{result['location']}'")
