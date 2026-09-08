#!/usr/bin/env python
"""Test template API endpoints"""

import requests
import json
import sys

def test_template_endpoints():
    """Test template endpoints"""
    base_url = "http://localhost:8000/api/v1"
    
    # Test 1: Login
    print("1. Testing login...")
    login_response = requests.post(
        f"{base_url}/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    
    if login_response.status_code != 200:
        print(f"   ✗ Login failed: {login_response.status_code}")
        print(f"   {login_response.text}")
        return False
    
    token = login_response.json().get("access_token")
    print(f"   ✓ Logged in")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Test 2: List templates
    print("\n2. Testing GET /templates (list templates)...")
    list_response = requests.get(
        f"{base_url}/templates",
        headers=headers
    )
    
    print(f"   Status: {list_response.status_code}")
    if list_response.status_code == 404:
        print(f"   ✗ 404 Not Found!")
        print(f"   Response: {list_response.text}")
        return False
    elif list_response.status_code == 200:
        print(f"   ✓ Success")
        data = list_response.json()
        print(f"   Templates: {data}")
    else:
        print(f"   ✗ Error: {list_response.status_code}")
        print(f"   {list_response.text}")
        return False
    
    # Test 3: Check if we can reach the drafts endpoint
    print("\n3. Testing POST /templates/drafts (upload PDF)...")
    
    # Create a simple test PDF file
    pdf_content = b"%PDF-1.4\n%dummy pdf content\n"
    
    files = {
        'file': ('test_resume.pdf', pdf_content, 'application/pdf')
    }
    
    upload_response = requests.post(
        f"{base_url}/templates/drafts",
        files=files,
        headers=headers
    )
    
    print(f"   Status: {upload_response.status_code}")
    if upload_response.status_code == 404:
        print(f"   ✗ 404 Not Found!")
        print(f"   Response: {upload_response.text}")
        return False
    elif upload_response.status_code in [200, 201]:
        print(f"   ✓ Success")
        print(f"   Response: {upload_response.json()}")
    else:
        print(f"   Note: Status {upload_response.status_code}")
        print(f"   Response: {upload_response.text[:200]}")
    
    print("\n✓ Endpoints are accessible (no 404)")
    return True

if __name__ == "__main__":
    try:
        success = test_template_endpoints()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"✗ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
