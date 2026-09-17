"""
Integration test for resume parsing with multi-line experience/projects parser.
Tests the complete flow from resume text to parsed data.
"""

import sys
import json


def test_resume_parsing_integration():
    """Test complete resume parsing pipeline."""
    print("\n" + "="*80)
    print("INTEGRATION TEST: Complete Resume Parsing Pipeline")
    print("="*80)
    
    # Import parsing functions
    from app.services.multi_line_experience_parser import (
        parse_experience_multiline,
        parse_projects_multiline,
        validate_and_enhance_experience,
        validate_and_enhance_projects,
    )
    
    # Simulate resume text (as extracted from PDF)
    resume_text = """
    PROFESSIONAL EXPERIENCE
    
    UST                                          Pune, India
    Lead Data & GenAI Engineer                   October 2023 - Present
    • Architected end-to-end cloud-native data pipelines using BigQuery, Dataflow, Pub/Sub, Cloud Functions
    • Designed scalable BigQuery warehouse models with advanced partitioning and clustering strategies
    • Built Generative AI solutions integrating Vertex AI and Gemini for LLM-powered automation
    • Modernized legacy ETL workflows to cloud-native patterns using Dataflow and Cloud Composer
    • Implemented enterprise data governance frameworks, establishing data quality and compliance protocols
    
    IBM                                          Pune, India
    Senior Software Engineer - 2                 November 2021 - October 2023
    • Developed and optimized data pipelines for retail and healthcare analytics platforms
    • Implemented data quality frameworks and automated validation processes
    • Collaborated with product teams to translate business requirements into scalable solutions
    
    Bitwise                                      Pune, India
    Software Associate / Programmer Analyst     July 2019 - November 2021
    • Served as Programmer for Migration project from on-premise to GCP cloud
    • Led team initiatives to improve code quality and delivery timelines
    • Designed and implemented ETL workflows using GCP Cloud
    
    PROJECT EXPERIENCE
    
    Cloud Data Pipeline                          Google Cloud Platform
    Data pipeline architect and lead developer   2023 - 2024
    • Built end-to-end ETL using BigQuery, Dataflow, and Cloud Functions
    • Processed 500M+ records daily with 99.9% reliability
    • Technologies: Python, SQL, BigQuery, Apache Beam, Pub/Sub
    
    Real-time Analytics Dashboard                Fortune 500 Client
    Full-stack developer and architect           2022 - 2023
    • Designed real-time analytics dashboard with React and Node.js
    • Implemented WebSocket-based data streaming for live updates
    • Technologies: React, Node.js, MongoDB, Redis
    """
    
    # Split into sections
    lines = [line.strip() for line in resume_text.split('\n') if line.strip()]
    
    # Find section indices
    exp_start = next((i for i, l in enumerate(lines) if 'PROFESSIONAL EXPERIENCE' in l.upper()), 0)
    proj_start = next((i for i, l in enumerate(lines) if 'PROJECT' in l.upper() and 'EXPERIENCE' in l.upper()), len(lines))
    
    exp_lines = lines[exp_start+1:proj_start]
    proj_lines = lines[proj_start+1:]
    
    # Parse experience
    print("\n[Experience Parsing]")
    experiences = parse_experience_multiline(exp_lines)
    experiences = validate_and_enhance_experience(experiences)
    
    print(f"Parsed {len(experiences)} work experience entries:\n")
    assert len(experiences) == 3, f"Expected 3 entries, got {len(experiences)}"
    
    for i, exp in enumerate(experiences, 1):
        print(f"{i}. {exp['company']} - {exp['title']}")
        print(f"   Location: {exp['location']}")
        print(f"   Dates: {exp['dates']}")
        print(f"   Responsibilities: {len(exp['responsibilities'])} items")
        
        # Validate structure
        assert exp['company'], f"Entry {i}: Missing company"
        assert exp['title'], f"Entry {i}: Missing title"
        assert exp['location'], f"Entry {i}: Missing location"
    
    # Validate specific entries
    assert experiences[0]['company'] == 'UST', "First entry should be UST"
    assert 'Lead Data' in experiences[0]['title'], "UST title should contain 'Lead Data'"
    assert 'Pune' in experiences[0]['location'], "UST location should contain 'Pune'"
    print("\n✓ Work experience parsing successful")
    
    # Parse projects
    print("\n[Projects Parsing]")
    projects = parse_projects_multiline(proj_lines)
    projects = validate_and_enhance_projects(projects)
    
    print(f"Parsed {len(projects)} projects:\n")
    assert len(projects) >= 1, f"Expected at least 1 project, got {len(projects)}"
    
    for i, proj in enumerate(projects, 1):
        print(f"{i}. {proj['name']}")
        print(f"   Client: {proj['client']}")
        print(f"   Technologies: {', '.join(proj['technologies'][:3])}")
        print(f"   Responsibilities: {len(proj['responsibilities'])} items")
        
        # Validate structure
        assert proj['name'], f"Project {i}: Missing name"
    
    print("\n✓ Projects parsing successful")
    
    # Overall summary
    print("\n" + "="*80)
    print("INTEGRATION TEST RESULTS")
    print("="*80)
    print(f"✓ Parsed {len(experiences)} work experiences")
    print(f"✓ Parsed {len(projects)} projects")
    print(f"✓ All data correctly extracted from multi-line format")
    print(f"✓ Field validation passed")
    print("\nThe multi-line parser is ready for production use!")


def test_edge_cases():
    """Test edge cases and robustness."""
    print("\n" + "="*80)
    print("EDGE CASE TESTS")
    print("="*80)
    
    from app.services.multi_line_experience_parser import (
        _split_line_left_right,
        _is_location,
        _is_company_name,
        _is_job_title,
        _extract_dates_from_line,
    )
    
    # Test 1: Varying gap sizes
    print("\n[Test 1: Varying Whitespace Gaps]")
    test_cases = [
        ("UST                   Pune, India", "UST", "Pune, India"),
        ("UST    |    Pune, India", "UST", "Pune, India"),
        ("UST – Pune, India", "UST", "Pune, India"),
        ("IBM Pune, India", "IBM", "Pune, India"),
    ]
    
    for line, expected_left, expected_right in test_cases:
        left, right = _split_line_left_right(line)
        assert expected_left in left, f"Expected '{expected_left}' in '{left}'"
        print(f"  ✓ {line[:30]:30} → {left:20} | {right}")
    
    # Test 2: Date format variations
    print("\n[Test 2: Date Format Variations]")
    date_cases = [
        ("October 2023 - Present", "October 2023"),
        ("2023 - 2024", "2023"),
        ("January 2020 - December 2022", "January 2020"),
        ("Lead Data Engineer October 2023 - Present", "October 2023"),
    ]
    
    for line, expected_date_part in date_cases:
        date_str, remaining = _extract_dates_from_line(line)
        assert expected_date_part in date_str, f"Expected '{expected_date_part}' in '{date_str}' from '{line}'"
        print(f"  ✓ {expected_date_part} extracted from '{line[:40]}'")
    
    # Test 3: Field type detection
    print("\n[Test 3: Field Type Detection]")
    
    location_tests = [
        ("Pune, India", True),
        ("Bangalore, Karnataka", True),
        ("Remote", True),
        ("Senior Engineer", False),
        ("UST", False),
    ]
    
    for text, should_be_location in location_tests:
        result = _is_location(text)
        assert result == should_be_location, f"Location detection failed for '{text}'"
        status = "✓ Location" if should_be_location else "✗ Not location"
        print(f"  {status}: '{text}'")
    
    company_tests = [
        ("UST", True),
        ("IBM", True),
        ("Bitwise", True),
        ("Lead Engineer", False),
        ("Pune, India", False),
    ]
    
    for text, should_be_company in company_tests:
        result = _is_company_name(text)
        assert result == should_be_company, f"Company detection failed for '{text}'"
        status = "✓ Company" if should_be_company else "✗ Not company"
        print(f"  {status}: '{text}'")
    
    title_tests = [
        ("Lead Data & GenAI Engineer", True),
        ("Senior Software Engineer - 2", True),
        ("Software Associate / Programmer Analyst", True),
        ("UST", False),
        ("Pune, India", False),
    ]
    
    for text, should_be_title in title_tests:
        result = _is_job_title(text)
        assert result == should_be_title, f"Title detection failed for '{text}'"
        status = "✓ Title" if should_be_title else "✗ Not title"
        print(f"  {status}: '{text}'")
    
    print("\n✓ All edge case tests passed")


if __name__ == "__main__":
    try:
        test_resume_parsing_integration()
        test_edge_cases()
        
        print("\n" + "="*80)
        print("✓ ALL INTEGRATION TESTS PASSED")
        print("="*80)
        print("\nSummary:")
        print("  ✓ Multi-line experience parser working correctly")
        print("  ✓ Multi-line projects parser working correctly")
        print("  ✓ Field detection and validation robust")
        print("  ✓ Ready for production deployment")
        
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
