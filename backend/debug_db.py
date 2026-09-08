from app.core.database import get_engine
from app.models.kanini_resume_db import KaniniResume
from sqlalchemy.orm import Session
from sqlalchemy import inspect

# Check if table exists and inspect
try:
    engine = get_engine()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Tables in database:", tables)
    
    if 'kanini_resumes' in tables:
        # Try to query
        with Session(engine) as session:
            resumes = session.query(KaniniResume).limit(3).all()
            print(f"\nTotal resumes found: {len(resumes)}")
            
            for i, resume in enumerate(resumes, 1):
                print(f"\n--- Resume {i} ---")
                print(f"ID: {resume.id}")
                print(f"Filename: {resume.filename}")
                print(f"Parsed data type: {type(resume.parsed_data)}")
                print(f"Parsed data keys: {resume.parsed_data.keys() if isinstance(resume.parsed_data, dict) else 'Not a dict'}")
                if isinstance(resume.parsed_data, dict):
                    print(f"Has contact: {'contact' in resume.parsed_data}")
                    print(f"Contact data: {resume.parsed_data.get('contact', {})}")
                    print(f"Summary length: {len(resume.parsed_data.get('summary', ''))}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
