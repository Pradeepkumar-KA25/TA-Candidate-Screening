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
    if candidate and candidate.raw_payload:
        # Check which fields exist in raw_payload
        payload = candidate.raw_payload
        
        # Fields the service looks for
        personal_fields = [
            "Date_Of_Birth", "Full_Address", "Aadhaar_No", "Aadhar_New",
            "Email_Optional", "LinkedIn__s", "Facebook__s", "Recruiter_Mobile_No"
        ]
        
        employment_fields = [
            "Date_of_Joining", "Employee_Type", "Employee_Details", "Emp_ID",
            "Department", "Function_Department", "Practice", "Work_Mode_Location",
            "Onsite_Remote", "WorkStream"
        ]
        
        print("=== Matching Fields ===")
        print("\nPersonal Contact Fields:")
        for field in personal_fields:
            if field in payload:
                value = payload[field]
                if value:
                    print(f"  ✓ {field}: {value}")
        
        print("\nEmployment Fields:")
        for field in employment_fields:
            if field in payload:
                value = payload[field]
                if value:
                    print(f"  ✓ {field}: {value}")
        
        # Now extract using the service method
        print("\n=== Extracted Extended Fields ===")
        extended = CandidateService._extract_extended_fields(payload)
        print(f"Personal Contact: {len(extended.personal_contact)} items")
        if extended.personal_contact:
            for k, v in extended.personal_contact.items():
                print(f"  - {k}: {v}")
        
        print(f"\nEmployment: {len(extended.employment)} items")
        if extended.employment:
            for k, v in extended.employment.items():
                print(f"  - {k}: {v}")
        
        print(f"\nInterview Process: {len(extended.interview_process)} items")
        print(f"Candidate Lifecycle: {len(extended.candidate_lifecycle)} items")
        print(f"Salary Benefits: {len(extended.salary_benefits)} items")
        print(f"Referral Vendor Sourcing: {len(extended.referral_vendor_sourcing)} items")
    else:
        print("No candidate found or no raw_payload")
