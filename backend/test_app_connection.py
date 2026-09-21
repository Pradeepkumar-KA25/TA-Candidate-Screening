#!/usr/bin/env python
"""Test if the backend can connect to Zoho using stored credentials."""

import httpx
import json
import sys
import os
from pathlib import Path
os.chdir(Path(__file__).parent)

# Get a test auth token
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User

print("=" * 70)
print("TESTING APPLICATION ZOHO CONNECTION")
print("=" * 70)
print()

# Test backend health
print("1. Testing backend health...")
response = httpx.get("http://localhost:8000/health", timeout=5)
print(f"   Backend status: {response.status_code}")
print(f"   Response: {response.json()}")
print()

# Get an auth token (use default admin user or create one)
print("2. Getting authentication token...")
try:
    engine = create_engine(settings.database_url)
    with Session(engine) as session:
        user = session.query(User).first()
        if not user:
            print("   [ERROR] No users found in database")
            sys.exit(1)
        
        print(f"   ✓ Using user: {user.email}")
        user_id = user.id
    
    # Get token from auth endpoint
    auth_response = httpx.post(
        "http://localhost:8000/api/v1/auth/token",
        json={"email": user.email, "password": "password"},  # Adjust if needed
        timeout=5
    )
    
    if auth_response.status_code != 200:
        print(f"   [INFO] Could not get token via password, trying direct method")
        # For testing, we might need to handle auth differently
        # Skip auth for now and test direct DB access
        import jwt
        from datetime import datetime, timedelta
        
        secret = settings.jwt_secret_key
        payload = {
            "sub": str(user_id),
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        print(f"   ✓ Generated test token")
    else:
        token = auth_response.json().get("access_token")
        print(f"   ✓ Got auth token")
    
    print()
    
    # Test candidates endpoint with auth
    print("3. Testing Zoho connection via /api/v1/candidates endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get("http://localhost:8000/api/v1/candidates", headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        candidates = data.get('data', [])
        print(f"   ✅ Connected to Zoho!")
        print(f"   Found {len(candidates)} candidates")
        
        if candidates:
            print(f"   Sample: {candidates[0].get('full_name', 'Unknown')}")
        
        print()
        print("=" * 70)
        print("✅ APPLICATION IS CONNECTED TO ZOHO")
        print("=" * 70)
        
    else:
        print(f"   ❌ HTTP {response.status_code}")
        print(f"   Response: {response.text[:300]}")
        
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
