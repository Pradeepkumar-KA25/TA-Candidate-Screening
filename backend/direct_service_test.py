"""Direct service test"""
import json
import sys
sys.path.insert(0, '.')

from app.core.database import get_session_factory
from app.models.candidate import Candidate
from app.services.candidate_service import CandidateService
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_description_repository import JobDescriptionRepository

SessionLocal = get_session_factory()
session = SessionLocal()

try:
    repo = CandidateRepository(session)
    jd_repo = JobDescriptionRepository(session)
    service = CandidateService(repository=repo, job_description_repository=jd_repo)
    
    # Get candidates
    candidates = session.query(Candidate).limit(3).all()
    
    for candidate in candidates:
        print(f"\n{'='*60}")
        print(f"Candidate: {candidate.full_name}")
        print(f"ID: {candidate.id}")
        
        try:
            response = service.get_candidate_details(candidate.id)
            
            # Serialize to JSON like the API would
            response_dict = response.model_dump()
            
            # Check extended_fields
            if "extended_fields" in response_dict:
                ext = response_dict["extended_fields"]
                print("✓ extended_fields present")
                
                for key in ["personal_contact", "employment", "interview_process", "candidate_lifecycle", "salary_benefits", "referral_vendor_sourcing"]:
                    if key in ext:
                        items = ext[key]
                        count = len(items) if isinstance(items, dict) else 0
                        print(f"  {key}: {count} items")
                        if count > 0:
                            first_item = list(items.items())[0]
                            print(f"    Example: {first_item[0]} = {first_item[1]}")
            else:
                print("✗ extended_fields NOT present")
                print(f"Keys in response: {list(response_dict.keys())}")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

finally:
    session.close()
