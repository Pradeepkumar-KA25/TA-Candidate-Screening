import sys
sys.path.insert(0, '.')
from app.core.database import get_engine
from app.models.candidate import Candidate
from app.services.candidate_service import CandidateService
from sqlalchemy.orm import Session
import json

engine = get_engine()
with Session(engine) as session:
    candidate = session.query(Candidate).first()
    if candidate:
        print(f"\n=== Candidate: {candidate.full_name} ===")
        print(f"ID: {candidate.id}")
        
        # Manually build the response as the API would
        extended = CandidateService._extract_extended_fields(candidate.raw_payload or {})
        
        # Simulate what the API response would look like
        response = {
            "id": str(candidate.id),
            "full_name": candidate.full_name,
            "extended_fields": {
                "personal_contact": extended.personal_contact,
                "employment": extended.employment,
                "interview_process": extended.interview_process,
                "candidate_lifecycle": extended.candidate_lifecycle,
                "salary_benefits": extended.salary_benefits,
                "referral_vendor_sourcing": extended.referral_vendor_sourcing,
            }
        }
        
        # Pretty print as JSON (like the API response)
        json_response = json.dumps(response, indent=2, default=str)
        print("\nAPI Response JSON:")
        print(json_response[:2000])  # First 2000 chars
        
        if len(json_response) > 2000:
            print(f"\n... ({len(json_response) - 2000} more characters)")
