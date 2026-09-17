"""
Test to verify improved designation extraction from same line with dates.
"""

from app.services.multi_line_experience_parser import (
    parse_experience_multiline,
    validate_and_enhance_experience,
    _extract_dates_from_line,
    _is_role_and_dates_line,
)


def test_designation_and_dates_same_line():
    """Test extraction when designation and dates are on the same line."""
    print("\n" + "="*80)
    print("TEST: Designation and Dates Extraction (Same Line)")
    print("="*80)
    
    # Test different formats
    test_cases = [
        ("Lead Data Engineer - October 2023 - Present", "Lead Data Engineer", "October 2023 - Present"),
        ("Lead Data Engineer – October 2023 – Present", "Lead Data Engineer", "October 2023 – Present"),
        ("Senior Software Engineer - 2                 November 2021 - October 2023", "Senior Software Engineer - 2", "November 2021 - October 2023"),
        ("Lead Data & GenAI Engineer                   October 2023 - Present", "Lead Data & GenAI Engineer", "October 2023 - Present"),
    ]
    
    print("\n[Step 1: Testing Date Extraction]")
    for line, expected_title, expected_dates in test_cases:
        dates_str, remaining = _extract_dates_from_line(line)
        print(f"\nInput:  {line}")
        print(f"Expected Title: {expected_title}")
        print(f"Got Title:      {remaining}")
        print(f"Expected Dates: {expected_dates}")
        print(f"Got Dates:      {dates_str}")
        
        assert dates_str, f"Dates not extracted from: {line}"
        assert remaining == expected_title, f"Title mismatch. Expected '{expected_title}', got '{remaining}'"
        print("✓ PASSED")
    
    # Test with actual resume lines
    print("\n[Step 2: Testing Full Experience Parsing]")
    resume_lines = [
        "UST                                          Pune, India",
        "Lead Data & GenAI Engineer                   October 2023 - Present",
        "• Architected end-to-end cloud-native data pipelines",
        "",
        "IBM                                          Pune, India",
        "Senior Software Engineer - 2                 November 2021 - October 2023",
        "• Developed and optimized data pipelines for retail analytics",
    ]
    
    experiences = parse_experience_multiline(resume_lines)
    experiences = validate_and_enhance_experience(experiences)
    
    print(f"\nParsed {len(experiences)} experiences:")
    
    # Check UST experience
    ust = experiences[0]
    print(f"\n1. {ust['company']}")
    print(f"   Title: {ust['title']}")
    print(f"   Dates: {ust['dates']}")
    
    assert ust['title'] == "Lead Data & GenAI Engineer", f"Expected 'Lead Data & GenAI Engineer', got '{ust['title']}'"
    assert "October 2023" in ust['dates'], f"Expected dates with 'October 2023', got '{ust['dates']}'"
    print("   ✓ Title and dates extracted correctly!")
    
    # Check IBM experience
    ibm = experiences[1]
    print(f"\n2. {ibm['company']}")
    print(f"   Title: {ibm['title']}")
    print(f"   Dates: {ibm['dates']}")
    
    assert "Senior" in ibm['title'], f"Expected 'Senior' in title, got '{ibm['title']}'"
    assert "November 2021" in ibm['dates'], f"Expected dates with 'November 2021', got '{ibm['dates']}'"
    print("   ✓ Title and dates extracted correctly!")
    
    print("\n" + "="*80)
    print("✅ ALL DESIGNATION AND DATES EXTRACTION TESTS PASSED")
    print("="*80)


if __name__ == "__main__":
    try:
        test_designation_and_dates_same_line()
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
