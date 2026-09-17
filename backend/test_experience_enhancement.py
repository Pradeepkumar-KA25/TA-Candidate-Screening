#!/usr/bin/env python3
"""
Test script to verify the enhanced experience extraction works correctly.
"""
import sys
sys.path.insert(0, '.')

from app.services.experience_extraction_enhancer import (
    validate_and_correct_experience,
    enhance_experience_list,
    _is_location_pattern,
    _is_company_name,
    _is_job_role,
    _split_company_location,
)

def test_location_detection():
    """Test location pattern detection."""
    print("=" * 60)
    print("Testing Location Detection")
    print("=" * 60)
    
    test_cases = [
        ("Pune, India", True),
        ("Bangalore, Karnataka", True),
        ("New York, USA", True),
        ("Remote", True),
        ("San Francisco", True),
        ("UST", False),
        ("IBM", False),
        ("Senior Engineer", False),
    ]
    
    for text, expected in test_cases:
        result = _is_location_pattern(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> {result} (expected {expected})")

def test_company_detection():
    """Test company name detection."""
    print("\n" + "=" * 60)
    print("Testing Company Name Detection")
    print("=" * 60)
    
    test_cases = [
        ("UST", True),
        ("IBM", True),
        ("Accenture", True),
        ("TCS", True),
        ("Pune, India", False),
        ("Senior Engineer", False),
        ("Lead Developer", False),
    ]
    
    for text, expected in test_cases:
        result = _is_company_name(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> {result} (expected {expected})")

def test_job_role_detection():
    """Test job role detection."""
    print("\n" + "=" * 60)
    print("Testing Job Role Detection")
    print("=" * 60)
    
    test_cases = [
        ("Senior Engineer", True),
        ("Lead Developer", True),
        ("Solutions Architect", True),
        ("Project Manager", True),
        ("UST", False),
        ("Pune, India", False),
    ]
    
    for text, expected in test_cases:
        result = _is_job_role(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> {result} (expected {expected})")

def test_split_company_location():
    """Test splitting combined company+location strings."""
    print("\n" + "=" * 60)
    print("Testing Company+Location Splitting")
    print("=" * 60)
    
    test_cases = [
        ("UST Pune, India", ("UST", "Pune, India")),
        ("IBM Bangalore, Karnataka", ("IBM", "Bangalore, Karnataka")),
        ("Accenture New York, USA", ("Accenture", "New York, USA")),
        ("Pune, India", (None, "Pune, India")),
        ("UST", ("UST", None)),
    ]
    
    for text, expected in test_cases:
        company, location = _split_company_location(text)
        result = (company, location)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> {result} (expected {expected})")

def test_experience_correction():
    """Test the main experience correction logic."""
    print("\n" + "=" * 60)
    print("Testing Experience Entry Correction")
    print("=" * 60)
    
    # The problematic case from the user
    print("\n📋 Test Case 1: UST with location swapped")
    bad_experience = {
        "company": "Pune, India",
        "title": "UST",
        "location": "",
        "dates": "October 2023 – Present",
        "responsibilities": ["Architected end-to-end cloud-native data pipelines..."],
    }
    
    corrected = validate_and_correct_experience(bad_experience)
    print(f"Before:")
    print(f"  Company: {bad_experience['company']}")
    print(f"  Title: {bad_experience['title']}")
    print(f"  Location: {bad_experience['location']}")
    print(f"\nAfter:")
    print(f"  Company: {corrected['company']}")
    print(f"  Title: {corrected['title']}")
    print(f"  Location: {corrected['location']}")
    
    # Verify correction
    if corrected['company'] == "UST" and corrected['location'] == "Pune, India":
        print("✓ PASS: Correctly identified company and location")
    else:
        print("✗ FAIL: Did not correct company/location properly")

def test_multiple_experiences():
    """Test correction of multiple experience entries."""
    print("\n" + "=" * 60)
    print("Testing Multiple Experience Corrections")
    print("=" * 60)
    
    experiences = [
        {
            "company": "Pune, India",
            "title": "UST",
            "location": "",
            "dates": "October 2023 – Present",
            "responsibilities": ["Experience 1"],
        },
        {
            "company": "IBM",
            "title": "Senior Software Engineer - 2",
            "location": "Pune, India",
            "dates": "November 2021 - October 2023",
            "responsibilities": ["Experience 2"],
        },
        {
            "company": "Bitwise",
            "title": "Software Associate / Programmer Analyst",
            "location": "Pune, India",
            "dates": "July 2019 - November 2021",
            "responsibilities": ["Experience 3"],
        },
    ]
    
    corrected = enhance_experience_list(experiences)
    
    for i, (orig, corr) in enumerate(zip(experiences, corrected)):
        print(f"\n📌 Experience {i+1}:")
        print(f"  Original: {orig['company']} | {orig['title']}")
        print(f"  Corrected: {corr['company']} | {corr['title']}")

if __name__ == "__main__":
    test_location_detection()
    test_company_detection()
    test_job_role_detection()
    test_split_company_location()
    test_experience_correction()
    test_multiple_experiences()
    
    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)
