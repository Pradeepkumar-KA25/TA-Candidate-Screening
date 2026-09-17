"""
Diagnostic test: Complete end-to-end flow including JSON serialization
Simulates the exact API request/response cycle
"""

import json
import tempfile
from pathlib import Path
from app.services.kanini_resume_parser import parse_resume


def test_end_to_end_with_serialization():
    """Test the complete flow including database storage simulation."""
    print("\n" + "="*80)
    print("DIAGNOSTIC TEST: End-to-End Resume Flow with Serialization")
    print("="*80)
    
    # Create a sample resume text file
    resume_text = """
JOHN DOE
john.doe@email.com | +91 9876543210 | Bangalore, India | linkedin.com/in/johndoe

PROFESSIONAL SUMMARY
Experienced full-stack engineer with 5+ years in cloud platforms and data processing.

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

Bitwise                                      Pune, India
Software Associate / Programmer Analyst     July 2019 - November 2021
• Served as Programmer for Migration project from on-premise to GCP cloud
• Led team initiatives to improve code quality and delivery timelines

SKILLS
Python: Django, Flask, FastAPI
JavaScript: React, Angular, Node.js
Cloud: BigQuery, Dataflow, GCP, AWS
Databases: PostgreSQL, MongoDB

EDUCATION
B.Tech in Computer Science | Indian Institute of Technology | 2019 | 8.5 GPA
"""
    
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(resume_text)
            temp_file = f.name
        
        try:
            print("\n[Step 1: Parse Resume]")
            parsed_data = parse_resume(temp_file, 'txt')
            
            # Check experiences
            experiences = parsed_data.get('experience', [])
            print(f"Parsed {len(experiences)} experiences")
            
            for i, exp in enumerate(experiences[:2]):
                print(f"\n  Experience {i+1}:")
                print(f"    - company: {exp.get('company', 'MISSING')}")
                print(f"    - title: {exp.get('title', 'MISSING')}")
                print(f"    - dates: {exp.get('dates', 'MISSING')}")
                
                if not exp.get('title'):
                    print(f"    ✗ ERROR: Title is missing!")
            
            print("\n[Step 2: Simulate Database Storage]")
            # Simulate storing in database as JSON
            json_str = json.dumps(parsed_data, indent=2)
            print(f"Serialized to JSON: {len(json_str)} characters")
            
            print("\n[Step 3: Simulate Database Retrieval]")
            # Simulate retrieving from database
            retrieved_data = json.loads(json_str)
            
            experiences = retrieved_data.get('experience', [])
            print(f"Retrieved {len(experiences)} experiences")
            
            for i, exp in enumerate(experiences[:2]):
                print(f"\n  Experience {i+1}:")
                print(f"    - company: {exp.get('company', 'MISSING')}")
                print(f"    - title: {exp.get('title', 'MISSING')}")
                print(f"    - dates: {exp.get('dates', 'MISSING')}")
                
                if not exp.get('title'):
                    print(f"    ✗ ERROR: Title is missing after retrieval!")
            
            print("\n[Step 4: Simulate Frontend Form Population]")
            # Simulate what the frontend does
            form_data = []
            for i, exp in enumerate(experiences):
                # Frontend logic with fallbacks
                titleValue = exp.get('title') or exp.get('designation') or exp.get('jobTitle') or exp.get('role') or ''
                
                form_item = {
                    "company": exp.get('company') or exp.get('company_name') or '',
                    "title": titleValue,
                    "dates": exp.get('dates') or exp.get('duration') or '',
                    "responsibilities": (exp.get('responsibilities') or [])
                }
                form_data.append(form_item)
                
                print(f"\n  Experience {i+1} Form Data:")
                print(f"    - company: '{form_item['company']}'")
                print(f"    - title: '{form_item['title']}'")
                print(f"    - dates: '{form_item['dates']}'")
                
                if not form_item['title']:
                    print(f"    ✗ WARNING: Title will be empty in form!")
                else:
                    print(f"    ✓ Title will display correctly")
            
            print("\n" + "="*80)
            
            # Final check
            all_have_titles = all(item.get('title') for item in form_data)
            if all_have_titles:
                print("SUCCESS: All experiences have titles throughout the entire flow")
                print("The title field SHOULD display correctly in the frontend")
            else:
                print("FAILURE: Some experiences lost their titles")
                missing = [i+1 for i, item in enumerate(form_data) if not item.get('title')]
                print(f"Missing titles in experiences: {missing}")
            
            print("="*80)
            
        finally:
            # Clean up
            if Path(temp_file).exists():
                Path(temp_file).unlink()
    
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    test_end_to_end_with_serialization()
