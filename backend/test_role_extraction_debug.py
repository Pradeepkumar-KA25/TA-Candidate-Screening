"""
Debug test to verify role/designation extraction is working correctly
"""

from app.services.multi_line_experience_parser import (
    parse_experience_multiline,
    validate_and_enhance_experience,
    _extract_dates_from_line,
    _is_role_and_dates_line,
)


def test_role_extraction_debug():
    """Test role extraction with exact format from user's resume."""
    print("\n" + "="*80)
    print("DEBUG TEST: Role/Designation Extraction")
    print("="*80)
    
    # Exact format from user's resume screenshot
    resume_lines = [
        "UST                                          Pune, India",
        "Lead Data & GenAI Engineer                   October 2023 - Present",
        "• Architected end-to-end cloud-native data pipelines using BigQuery, Dataflow",
        "• Designed scalable BigQuery warehouse models with advanced partitioning",
    ]
    
    print("\n[Step 1: Test _extract_dates_from_line directly]")
    line_2 = "Lead Data & GenAI Engineer                   October 2023 - Present"
    dates_str, remaining = _extract_dates_from_line(line_2)
    
    print(f"\nInput line: {line_2}")
    print(f"Extracted dates: '{dates_str}'")
    print(f"Remaining text: '{remaining}'")
    
    if dates_str:
        print("✓ Dates extracted successfully")
    else:
        print("✗ FAILED: Dates not extracted")
    
    if remaining and "Lead Data" in remaining:
        print("✓ Role extracted successfully")
    else:
        print("✗ FAILED: Role not properly extracted")
    
    print("\n[Step 2: Test _is_role_and_dates_line]")
    is_role_dates, role, dates = _is_role_and_dates_line(line_2)
    
    print(f"\nInput line: {line_2}")
    print(f"Is role+dates line: {is_role_dates}")
    print(f"Extracted role: '{role}'")
    print(f"Extracted dates: '{dates}'")
    
    if is_role_dates:
        print("✓ Correctly identified as role+dates line")
    else:
        print("✗ NOT identified as role+dates line")
    
    if role and "Lead Data" in role:
        print("✓ Role extracted successfully")
    else:
        print("✗ FAILED: Role not properly extracted")
    
    print("\n[Step 3: Full experience parsing]")
    experiences = parse_experience_multiline(resume_lines)
    
    print(f"\nNumber of experiences: {len(experiences)}")
    
    if len(experiences) > 0:
        exp = experiences[0]
        print(f"\nExperience 1:")
        print(f"  Company: '{exp.get('company', '')}'")
        print(f"  Title: '{exp.get('title', '')}'")
        print(f"  Location: '{exp.get('location', '')}'")
        print(f"  Dates: '{exp.get('dates', '')}'")
        print(f"  Responsibilities: {len(exp.get('responsibilities', []))} items")
        
        if exp.get('title') and "Lead Data" in exp.get('title', ''):
            print("\n✓ Title correctly extracted!")
        elif not exp.get('title'):
            print("\n✗ FAILED: Title is EMPTY")
        else:
            print(f"\n✗ FAILED: Title is wrong: '{exp.get('title', '')}'")
    
    print("\n[Step 4: After validation and enhancement]")
    experiences = validate_and_enhance_experience(experiences)
    
    if len(experiences) > 0:
        exp = experiences[0]
        print(f"\nExperience 1 (after enhancement):")
        print(f"  Company: '{exp.get('company', '')}'")
        print(f"  Title: '{exp.get('title', '')}'")
        print(f"  Location: '{exp.get('location', '')}'")
        print(f"  Dates: '{exp.get('dates', '')}'")
        
        if exp.get('title') and "Lead Data" in exp.get('title', ''):
            print("\n✓ Title correctly enhanced!")
        elif not exp.get('title'):
            print("\n✗ FAILED: Title is still EMPTY after enhancement")
        else:
            print(f"\n✗ FAILED: Title is still wrong: '{exp.get('title', '')}'")
    
    # Final verification
    print("\n" + "="*80)
    if experiences and experiences[0].get('title') and "Lead Data" in experiences[0].get('title', ''):
        print("✓ ROLE EXTRACTION WORKING CORRECTLY")
        print("  Issue is likely in frontend display logic")
    else:
        print("✗ ROLE EXTRACTION FAILED")
        print("  Backend parsing needs to be fixed")
    print("="*80)


if __name__ == "__main__":
    try:
        test_role_extraction_debug()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
