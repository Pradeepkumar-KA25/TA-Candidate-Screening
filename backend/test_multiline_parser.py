"""
Test suite for multi-line experience and projects parser.
Tests with the resume format provided by the user.
"""

from app.services.multi_line_experience_parser import (
    parse_experience_multiline,
    parse_projects_multiline,
    validate_and_enhance_experience,
    validate_and_enhance_projects,
)


# ─────────────────────────────────────────────────────────────────────────────
# Test data from user's resume
# ─────────────────────────────────────────────────────────────────────────────

RESUME_EXPERIENCE_LINES = [
    "UST                                          Pune, India",
    "Lead Data & GenAI Engineer                   October 2023 - Present",
    "• Architected end-to-end cloud-native data pipelines using BigQuery, Dataflow (Apache Beam), Pub/Sub, Cloud Functions, and GKE",
    "• Designed scalable BigQuery warehouse models with advanced partitioning and clustering strategies, optimizing TB-PB scale datasets",
    "• Built Generative AI solutions integrating Vertex AI and Gemini for LLM-powered automation, including RAG pipelines",
    "• Modernized legacy ETL workflows to cloud-native patterns using Dataflow and Cloud Composer, improving reliability by 45%",
    "• Implemented enterprise data governance frameworks, establishing data quality, lineage tracking, and compliance protocols",
    "• Led cross-functional teams in Agile delivery, mentoring 5+ engineers on GCP best practices and GenAI implementation patterns",
    "",
    "IBM                                          Pune, India",
    "Senior Software Engineer - 2                 November 2021 - October 2023",
    "• Developed and optimized data pipelines for retail and healthcare analytics platforms, processing millions of records daily",
    "• Implemented data quality frameworks and automated validation processes, reducing data anomalies by 60%",
    "• Collaborated with product teams to translate business requirements into scalable technical solutions",
    "",
    "Bitwise                                      Pune, India",
    "Software Associate / Programmer Analyst     July 2019 - November 2021",
    "• Served as Programmer for Migration project from on-premise to GCP cloud, delivering multiple enterprise data projects",
    "• Led team initiatives to improve code quality and delivery timelines",
    "• Designed and implemented ETL workflows using GCP Cloud, supporting business intelligence for Fortune 500 clients",
    "• Recognized as Associate of the Quarter for exceptional project delivery and technical leadership",
]

RESUME_PROJECTS_LINES = [
    "Project 1: Cloud Data Pipeline                Google Cloud Platform",
    "Data pipeline architect and lead developer   2023 - 2024",
    "• Built end-to-end ETL using BigQuery, Dataflow, and Cloud Functions",
    "• Processed 500M+ records daily with 99.9% reliability",
    "• Technologies: Python, SQL, BigQuery, Apache Beam, Pub/Sub",
    "",
    "Project 2: Real-time Analytics Dashboard    Internal - Fortune 500 Client",
    "Full-stack developer and architect           2022 - 2023",
    "• Designed real-time analytics dashboard with React and Node.js",
    "• Implemented WebSocket-based data streaming for live updates",
    "• Technologies: React, Node.js, MongoDB, Redis, WebSocket",
    "",
    "Project 3: Data Quality Framework            Company-wide Initiative",
    "Lead engineer and framework designer         2021 - 2022",
    "• Developed automated validation and cleansing framework",
    "• Reduced manual data correction efforts by 80%",
    "• Technologies: Python, SQL, Apache Spark, Great Expectations",
]


def test_experience_parsing():
    """Test parsing work experience from multi-line format."""
    print("\n" + "="*80)
    print("TEST: Experience Parsing (Multi-line Format)")
    print("="*80)
    
    experiences = parse_experience_multiline(RESUME_EXPERIENCE_LINES)
    experiences = validate_and_enhance_experience(experiences)
    
    print(f"\nParsed {len(experiences)} experience entries:\n")
    
    expected_count = 3
    assert len(experiences) == expected_count, f"Expected {expected_count} entries, got {len(experiences)}"
    print(f"✓ Correct number of entries: {len(experiences)}")
    
    # Test UST entry
    ust_exp = experiences[0]
    print(f"\n[Entry 1: UST]")
    print(f"  Company: {ust_exp['company']}")
    print(f"  Title: {ust_exp['title']}")
    print(f"  Location: {ust_exp['location']}")
    print(f"  Dates: {ust_exp['dates']}")
    print(f"  Responsibilities: {len(ust_exp['responsibilities'])} items")
    
    assert ust_exp["company"] == "UST", f"Expected company 'UST', got '{ust_exp['company']}'"
    assert ust_exp["title"] == "Lead Data & GenAI Engineer", f"Expected title 'Lead Data & GenAI Engineer', got '{ust_exp['title']}'"
    assert ust_exp["location"] == "Pune, India", f"Expected location 'Pune, India', got '{ust_exp['location']}'"
    assert "October 2023" in ust_exp["dates"], f"Expected dates to contain 'October 2023', got '{ust_exp['dates']}'"
    assert len(ust_exp["responsibilities"]) > 0, "Expected responsibilities"
    print("  ✓ UST entry correct")
    
    # Test IBM entry
    ibm_exp = experiences[1]
    print(f"\n[Entry 2: IBM]")
    print(f"  Company: {ibm_exp['company']}")
    print(f"  Title: {ibm_exp['title']}")
    print(f"  Location: {ibm_exp['location']}")
    print(f"  Dates: {ibm_exp['dates']}")
    
    assert ibm_exp["company"] == "IBM", f"Expected company 'IBM', got '{ibm_exp['company']}'"
    assert ibm_exp["title"] == "Senior Software Engineer - 2", f"Expected title 'Senior Software Engineer - 2', got '{ibm_exp['title']}'"
    assert ibm_exp["location"] == "Pune, India", f"Expected location 'Pune, India', got '{ibm_exp['location']}'"
    print("  ✓ IBM entry correct")
    
    # Test Bitwise entry
    bitwise_exp = experiences[2]
    print(f"\n[Entry 3: Bitwise]")
    print(f"  Company: {bitwise_exp['company']}")
    print(f"  Title: {bitwise_exp['title']}")
    print(f"  Location: {bitwise_exp['location']}")
    
    assert bitwise_exp["company"] == "Bitwise", f"Expected company 'Bitwise', got '{bitwise_exp['company']}'"
    assert "Programmer" in bitwise_exp["title"], f"Expected title to contain 'Programmer', got '{bitwise_exp['title']}'"
    print("  ✓ Bitwise entry correct")
    
    print("\n✓ ALL EXPERIENCE TESTS PASSED")
    return experiences


def test_projects_parsing():
    """Test parsing projects from multi-line format."""
    print("\n" + "="*80)
    print("TEST: Projects Parsing (Multi-line Format)")
    print("="*80)
    
    projects = parse_projects_multiline(RESUME_PROJECTS_LINES)
    projects = validate_and_enhance_projects(projects)
    
    print(f"\nParsed {len(projects)} projects:\n")
    
    expected_count = 3
    assert len(projects) == expected_count, f"Expected {expected_count} projects, got {len(projects)}"
    print(f"✓ Correct number of projects: {len(projects)}")
    
    # Test Project 1
    proj1 = projects[0]
    print(f"\n[Project 1]")
    print(f"  Name: {proj1['name']}")
    print(f"  Client: {proj1['client']}")
    print(f"  Dates: {proj1['dates']}")
    print(f"  Technologies: {proj1['technologies']}")
    print(f"  Responsibilities: {len(proj1['responsibilities'])} items")
    
    assert "Cloud Data Pipeline" in proj1["name"], f"Expected name with 'Cloud Data Pipeline', got '{proj1['name']}'"
    assert "GCP" in proj1["client"] or "Google" in proj1["client"], f"Expected client to contain GCP/Google, got '{proj1['client']}'"
    print("  ✓ Project 1 correct")
    
    # Test Project 2
    proj2 = projects[1]
    print(f"\n[Project 2]")
    print(f"  Name: {proj2['name']}")
    print(f"  Client: {proj2['client']}")
    print(f"  Role: {proj2['role']}")
    print(f"  Technologies: {proj2['technologies']}")
    
    assert "Dashboard" in proj2["name"] or "Analytics" in proj2["name"], f"Expected name with Dashboard/Analytics, got '{proj2['name']}'"
    print("  ✓ Project 2 correct")
    
    # Test Project 3
    proj3 = projects[2]
    print(f"\n[Project 3]")
    print(f"  Name: {proj3['name']}")
    print(f"  Client: {proj3['client']}")
    print(f"  Technologies: {proj3['technologies']}")
    
    assert "Data Quality" in proj3["name"] or "Framework" in proj3["name"], f"Expected name with Data Quality/Framework, got '{proj3['name']}'"
    print("  ✓ Project 3 correct")
    
    print("\n✓ ALL PROJECTS TESTS PASSED")
    return projects


def test_field_detection():
    """Test helper functions for field type detection."""
    print("\n" + "="*80)
    print("TEST: Field Detection Helpers")
    print("="*80)
    
    from app.services.multi_line_experience_parser import (
        _is_location, _is_job_title, _is_company_name
    )
    
    # Location detection
    assert _is_location("Pune, India") == True, "Should detect Pune, India as location"
    assert _is_location("Bangalore") == True, "Should detect Bangalore as location"
    assert _is_location("Remote") == True, "Should detect Remote as location"
    assert _is_location("UST") == False, "Should not detect UST as location"
    print("✓ Location detection working")
    
    # Job title detection
    assert _is_job_title("Lead Data & GenAI Engineer") == True, "Should detect Lead... Engineer as title"
    assert _is_job_title("Senior Software Engineer - 2") == True, "Should detect Senior... Engineer as title"
    assert _is_job_title("Software Associate / Programmer Analyst") == True, "Should detect Programmer as title"
    assert _is_job_title("Pune, India") == False, "Should not detect location as title"
    print("✓ Job title detection working")
    
    # Company name detection
    assert _is_company_name("UST") == True, "Should detect UST as company"
    assert _is_company_name("IBM") == True, "Should detect IBM as company"
    assert _is_company_name("Bitwise") == True, "Should detect Bitwise as company"
    assert _is_company_name("Lead Data Engineer") == False, "Should not detect title as company"
    print("✓ Company name detection working")
    
    print("\n✓ ALL DETECTION TESTS PASSED")


def test_line_splitting():
    """Test left/right line splitting."""
    print("\n" + "="*80)
    print("TEST: Line Splitting (Left/Right)")
    print("="*80)
    
    from app.services.multi_line_experience_parser import _split_line_left_right
    
    # Test with large spaces
    left, right = _split_line_left_right("UST                                          Pune, India")
    assert left == "UST", f"Expected left='UST', got '{left}'"
    assert right == "Pune, India", f"Expected right='Pune, India', got '{right}'"
    print("✓ Large space splitting works: 'UST ... Pune, India'")
    
    # Test with pipe
    left, right = _split_line_left_right("Cloud Data Pipeline | Google Cloud Platform")
    assert "Cloud Data Pipeline" in left, f"Expected left to contain 'Cloud Data Pipeline', got '{left}'"
    assert "Google Cloud" in right or "GCP" in right or "Platform" in right, f"Expected right to contain GCP/Platform, got '{right}'"
    print("✓ Pipe separator works")
    
    # Test single element
    left, right = _split_line_left_right("Lead Data & GenAI Engineer")
    assert "Lead" in left, f"Expected left to contain 'Lead', got '{left}'"
    print("✓ Single element handling works")
    
    print("\n✓ ALL LINE SPLITTING TESTS PASSED")


def test_date_extraction():
    """Test date extraction from lines."""
    print("\n" + "="*80)
    print("TEST: Date Extraction")
    print("="*80)
    
    from app.services.multi_line_experience_parser import _extract_dates_from_line
    
    # Test full date range
    date_str, remaining = _extract_dates_from_line("October 2023 - Present")
    assert "October 2023" in date_str, f"Expected date to contain 'October 2023', got '{date_str}'"
    print(f"✓ Full date range extracted: '{date_str}'")
    
    # Test with designation and dates
    date_str, remaining = _extract_dates_from_line("Lead Data & GenAI Engineer                   October 2023 - Present")
    assert "October 2023" in date_str, f"Expected date to contain 'October 2023', got '{date_str}'"
    assert "Lead" in remaining, f"Expected remaining to contain 'Lead', got '{remaining}'"
    print(f"✓ Date + designation extracted: dates='{date_str}', designation='{remaining}'")
    
    # Test year only
    date_str, remaining = _extract_dates_from_line("2023 - 2024")
    assert "2023" in date_str and "2024" in date_str, f"Expected year range, got '{date_str}'"
    print(f"✓ Year range extracted: '{date_str}'")
    
    print("\n✓ ALL DATE EXTRACTION TESTS PASSED")


if __name__ == "__main__":
    try:
        # Run all tests
        test_field_detection()
        test_line_splitting()
        test_date_extraction()
        experiences = test_experience_parsing()
        projects = test_projects_parsing()
        
        # Print summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"✓ All tests PASSED")
        print(f"✓ {len(experiences)} experience entries parsed correctly")
        print(f"✓ {len(projects)} projects parsed correctly")
        print("\nReady to integrate into resume parser!")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
