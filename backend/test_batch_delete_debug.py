"""
Debug script to test batch delete functionality.
Run this after starting the backend server.
"""

import asyncio
import json
from httpx import AsyncClient
import uuid

BASE_URL = "http://localhost:8000/api/v1"

async def test_batch_delete():
    """Test the batch delete endpoint."""
    async with AsyncClient(timeout=10.0) as client:
        # First, get a token (assuming test user exists)
        print("\n1. Getting auth token...")
        auth_response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": "admin@test.com", "password": "password123"}  # Adjust credentials as needed
        )
        print(f"   Auth response status: {auth_response.status_code}")
        
        if auth_response.status_code == 200:
            token = auth_response.json().get("access_token")
            print(f"   Token received: {token[:20]}...")
        else:
            print(f"   Auth failed: {auth_response.text}")
            return
        
        # Get list of candidates
        print("\n2. Getting candidate list...")
        headers = {"Authorization": f"Bearer {token}"}
        list_response = await client.get(
            f"{BASE_URL}/candidates?page=1&page_size=5",
            headers=headers
        )
        print(f"   List response status: {list_response.status_code}")
        
        if list_response.status_code == 200:
            candidates = list_response.json().get("items", [])
            print(f"   Found {len(candidates)} candidates")
            
            if candidates:
                # Try to delete the first candidate
                candidate_id = candidates[0]["id"]
                print(f"\n3. Attempting batch delete for candidate: {candidate_id}")
                print(f"   Candidate name: {candidates[0]['full_name']}")
                
                delete_response = await client.post(
                    f"{BASE_URL}/candidates/batch/delete",
                    json={"candidate_ids": [candidate_id]},
                    headers=headers
                )
                print(f"   Delete response status: {delete_response.status_code}")
                print(f"   Delete response body: {delete_response.json()}")
                
                if delete_response.status_code == 200:
                    result = delete_response.json()
                    print(f"\n✅ Result: Deleted {result['deleted_count']} candidate(s)")
                else:
                    print(f"\n❌ Delete failed with status {delete_response.status_code}")
            else:
                print("   No candidates found to delete")
        else:
            print(f"   List failed: {list_response.text}")

if __name__ == "__main__":
    asyncio.run(test_batch_delete())
