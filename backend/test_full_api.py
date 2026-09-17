"""Test the complete flow: backend returns extended_fields for API call"""
import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from uuid import uuid4
from app.main import app
from app.core.database import get_session_factory
from app.models.user import User
from app.models.candidate import Candidate

# Get session factory
SessionLocal = get_session_factory()

# Create test database session
session = SessionLocal()
try:
    # Check if test user exists
    test_user = session.query(User).filter_by(email="test@test.com").first()
    if not test_user:
        test_user = User(
            id=uuid4(),
            email="test@test.com",
            hashed_password="dummy",
            role="Recruiter",
            is_active=True
        )
        session.add(test_user)
        session.commit()
    
    # Get first candidate with raw_payload
    candidate = session.query(Candidate).filter(Candidate.raw_payload != None).first()
    
    if candidate:
        print(f"\n✓ Found candidate: {candidate.full_name}")
        print(f"✓ Candidate ID: {candidate.id}")
        print(f"✓ Has raw_payload: {candidate.raw_payload is not None}")
        
        # Now test the API endpoint
        from app.core.dependencies import get_db_session
        app.dependency_overrides[get_db_session] = lambda: session
        
        client = TestClient(app)
        
        # Create token for test user
        from app.services.auth_service import AuthService
        auth_service = AuthService(session)
        token = auth_service.create_access_token(test_user.email)
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get(f"/api/v1/candidates/{candidate.id}", headers=headers)
        
        print(f"\n✓ API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "extended_fields" in data:
                print("✓ Response contains 'extended_fields'")
                extended = data["extended_fields"]
                
                for category in ["personal_contact", "employment", "interview_process", "candidate_lifecycle", "salary_benefits", "referral_vendor_sourcing"]:
                    count = len(extended.get(category, {}))
                    print(f"  - {category}: {count} items")
                    if count > 0:
                        first_key = list(extended[category].keys())[0]
                        first_val = extended[category][first_key]
                        print(f"    Example: {first_key} = {first_val}")
            else:
                print("✗ Response does NOT contain 'extended_fields'")
                print(f"Response keys: {list(data.keys())}")
        else:
            print(f"✗ API Error: {response.status_code}")
            print(response.text)
    else:
        print("✗ No candidate found with raw_payload")
            
finally:
    session.close()
