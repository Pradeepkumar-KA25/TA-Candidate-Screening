"""
Test to verify the complete extraction pipeline for the exact user format.
Simulates what happens when a resume with multi-line experience is uploaded.
"""

from app.services.multi_line_experience_parser import (
    parse_experience_multiline,
    validate_and_enhance_experience,
)
from app.services.experience_extraction_enhancer import enhance_experience_list
import json


def test_complete_extraction_pipeline():
    """Test the complete extraction flow with exact user format."""
    print("\n" + "="*80)
    print("TEST: Complete Experience Extraction Pipeline")
    print("="*80)
    
    # Exact experience lines as they appear in the user's resume
    experience_lines = [
        "UST                                          Pune, India",
        "Lead Data & GenAI Engineer                   October 2023 - Present",
        "• Architected end-to-end cloud-native data pipelines using BigQuery, Dataflow",
        "• Designed scalable BigQuery warehouse models with advanced partitioning",
        "• Built Generative AI solutions integrating Vertex AI and Gemini",
        "",
        "IBM                                          Pune, India",
        "Senior Software Engineer - 2                 November 2021 - October 2023",
        "• Developed and optimized data pipelines for retail and healthcare analytics",
        "• Implemented data quality frameworks and automated validation processes",
    ]
    
    print("\n[Step 1: Parse with multi-line parser]")
    experiences = parse_experience_multiline(experience_lines)
    print(f"Extracted {len(experiences)} experiences")
    
    for i, exp in enumerate(experiences):
        print(f"\n  Experience {i+1}:")
        print(f"    - company: '{exp.get('company', '')}'")
        print(f"    - title: '{exp.get('title', '')}'")
        print(f"    - location: '{exp.get('location', '')}'")
        print(f"    - dates: '{exp.get('dates', '')}'")
    
    print("\n[Step 2: Validate and enhance]")
    experiences = validate_and_enhance_experience(experiences)
    
    for i, exp in enumerate(experiences):
        print(f"\n  Experience {i+1} (after enhancement):")
        print(f"    - company: '{exp.get('company', '')}'")
        print(f"    - title: '{exp.get('title', '')}'")
        print(f"    - location: '{exp.get('location', '')}'")
        print(f"    - dates: '{exp.get('dates', '')}'")
    
    print("\n[Step 3: Apply experience enhancement]")
    experiences = enhance_experience_list(experiences)
    
    for i, exp in enumerate(experiences):
        print(f"\n  Experience {i+1} (final):")
        print(f"    - company: '{exp.get('company', '')}'")
        print(f"    - title: '{exp.get('title', '')}'")
        print(f"    - location: '{exp.get('location', '')}'")
        print(f"    - dates: '{exp.get('dates', '')}'")
    
    print("\n[Step 4: Simulate frontend form population]")
    print("\n  Frontend expects this structure for each experience:")
    for i, exp in enumerate(experiences):
        form_data = {
            "company": exp.get('company') or exp.get('company_name') or '',
            "title": exp.get('title') or '',
            "dates": exp.get('dates') or '',
            "responsibilities": (exp.get('responsibilities') or [])
        }
        print(f"\n  Experience {i+1} Form Data:")
        print(f"    - company: '{form_data['company']}'")
        print(f"    - title: '{form_data['title']}'")
        print(f"    - dates: '{form_data['dates']}'")
        print(f"    - responsibilities: {len(form_data['responsibilities'])} items")
        
        # Check if title would show as placeholder in frontend
        if not form_data['title']:
            print(f"    ✗ WARNING: Title is empty! Frontend will show placeholder")
        else:
            print(f"    ✓ Title will display: {form_data['title']}")
    
    print("\n[Step 5: JSON serialization test]")
    print("  Simulating JSON storage in database...")
    json_str = json.dumps(experiences, indent=2)
    deserialized = json.loads(json_str)
    
    print(f"\n  After JSON round-trip:")
    for i, exp in enumerate(deserialized):
        print(f"\n  Experience {i+1}:")
        print(f"    - company: '{exp.get('company', '')}'")
        print(f"    - title: '{exp.get('title', '')}'")
        print(f"    - location: '{exp.get('location', '')}'")
        print(f"    - dates: '{exp.get('dates', '')}'")
    
    print("\n" + "="*80)
    
    # Final verification
    all_have_titles = all(exp.get('title') for exp in deserialized)
    
    if all_have_titles:
        print("SUCCESS: All experiences have titles in final JSON")
        print("The frontend should display all titles correctly")
    else:
        print("FAILURE: Some experiences are missing titles")
        print("The frontend will show placeholder text for missing titles")
    
    print("="*80)


if __name__ == "__main__":
    try:
        test_complete_extraction_pipeline()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
