"""Comprehensive test of the full API response"""
import json
import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_session_factory
from app.models.candidate import Candidate
from app.models.user import User
from app.core.dependencies import get_db_session
from sqlalchemy import select

# Get session
SessionLocal = get_session_factory()
session = SessionLocal()

try:
    # Get a user
    user = session.query(User).filter_by(role="Recruiter").first()
    if not user:
        print("No recruiter user found")
        sys.exit(1)
    
    # Override dependencies
    app.dependency_overrides[get_db_session] = lambda: session
    
    # Create test client
    client = TestClient(app)
    
    # Create auth token
    from app.services.auth_service import AuthService
    auth_service = AuthService(session)
    token = auth_service.create_access_token(user.email)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all candidates and test each one
    candidates = session.query(Candidate).limit(3).all()
    
    for candidate in candidates:
        print(f"\n{'='*60}")
        print(f"Testing candidate: {candidate.full_name}")
        print(f"ID: {candidate.id}")
        
        # Make API call
        response = client.get(f"/api/v1/candidates/{candidate.id}", headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if extended_fields exists
            if "extended_fields" in data:
                ext = data["extended_fields"]
                print("\n✓ extended_fields present in response")
                
                for key in ["personal_contact", "employment", "interview_process", "candidate_lifecycle", "salary_benefits", "referral_vendor_sourcing"]:
                    if key in ext:
                        items = ext[key]
                        count = len(items) if isinstance(items, dict) else 0
                        print(f"  {key}: {count} items")
                        if count > 0:
                            first_item = list(items.items())[0]
                            print(f"    - {first_item[0]}: {first_item[1]}")
            else:
                print("✗ extended_fields NOT in response")
                print(f"Response keys: {list(data.keys())}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:500])

finally:
    session.close()
