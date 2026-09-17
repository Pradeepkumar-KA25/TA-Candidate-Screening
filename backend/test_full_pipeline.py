"""
Test the complete resume parsing pipeline to verify all data is returned correctly.
"""

import tempfile
import os
from pathlib import Path
from app.services.kanini_resume_parser import parse_resume


def test_full_resume_parsing():
    """Test the complete pipeline with a realistic resume section."""
    print("\n" + "="*80)
    print("TEST: Complete Resume Parsing Pipeline")
    print("="*80)
    
    # Create a simple text file with resume content
    resume_text = """
    EXPERIENCE
    
    UST                                          Pune, India
    Lead Data & GenAI Engineer                   October 2023 - Present
    • Architected end-to-end cloud-native data pipelines using BigQuery, Dataflow
    • Designed scalable BigQuery warehouse models with advanced partitioning
    • Built Generative AI solutions integrating Vertex AI and Gemini
    
    IBM                                          Pune, India
    Senior Software Engineer - 2                 November 2021 - October 2023
    • Developed and optimized data pipelines for retail and healthcare analytics
    • Implemented data quality frameworks and automated validation processes
    
    SKILLS
    
    Python: Django, Flask, FastAPI, Pandas, NumPy
    JavaScript: React, Angular, Node.js
    Cloud: BigQuery, Dataflow, GCP, AWS
    Databases: PostgreSQL, MongoDB, Redis
    """
    
    try:
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(resume_text)
            temp_file = f.name
        
        try:
            # Parse the resume file
            parsed_data = parse_resume(temp_file, 'txt')
            
            print("\n[Full Response Structure]")
            print(f"Keys in parsed_data: {list(parsed_data.keys())}")
            
            # Check experience section
            print("\n[Experience Section]")
            experiences = parsed_data.get('experience', [])
            print(f"Number of experiences: {len(experiences)}")
            
            for i, exp in enumerate(experiences, 1):
                print(f"\n--- Experience {i} ---")
                print(f"Keys: {list(exp.keys())}")
                print(f"Company: '{exp.get('company', '')}'")
                print(f"Title: '{exp.get('title', '')}'")
                print(f"Location: '{exp.get('location', '')}'")
                print(f"Dates: '{exp.get('dates', '')}'")
                print(f"Responsibilities: {len(exp.get('responsibilities', []))} items")
                
                # Verify critical fields
                if not exp.get('title'):
                    print(f"✗ WARNING: Experience {i} has NO title!")
                else:
                    print(f"✓ Title present: {exp.get('title')}")
                
                if not exp.get('company'):
                    print(f"✗ WARNING: Experience {i} has NO company!")
                else:
                    print(f"✓ Company present: {exp.get('company')}")
            
            # Verify all experiences have required fields
            print("\n[Data Quality Check]")
            all_valid = True
            for i, exp in enumerate(experiences, 1):
                has_company = bool(exp.get('company'))
                has_title = bool(exp.get('title'))
                has_dates = bool(exp.get('dates'))
                
                if not has_company or not has_title:
                    print(f"✗ Experience {i}: MISSING REQUIRED FIELDS")
                    print(f"  - Company: {has_company}")
                    print(f"  - Title: {has_title}")
                    print(f"  - Dates: {has_dates}")
                    all_valid = False
                else:
                    print(f"✓ Experience {i}: All required fields present")
            
            print("\n" + "="*80)
            if all_valid:
                print("✓ ALL DATA FIELDS PRESENT AND CORRECT")
                print("  Frontend should receive all experience data correctly")
            else:
                print("✗ MISSING DATA FIELDS")
                print("  Frontend will show placeholder text for missing fields")
            print("="*80)
            
            return parsed_data
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        
    except Exception as e:
        print(f"\n✗ ERROR during parsing: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    try:
        result = test_full_resume_parsing()
    except Exception as e:
        print(f"\nFailed: {e}")
        exit(1)
