#!/usr/bin/env python
"""
Trigger full resume sync and monitor progress.
Requires authentication - uses test credentials.
"""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

import httpx
import json

async def trigger_sync():
    """Trigger sync endpoint and monitor results."""
    
    print("=" * 70)
    print("TRIGGERING FULL RESUME SYNC")
    print("=" * 70)
    print()
    
    base_url = "http://localhost:8000"
    
    try:
        with httpx.Client(timeout=30) as client:
            # Check if server is running
            print("Checking backend health...")
            response = client.get(f"{base_url}/health")
            print(f"  Status: {response.status_code}")
            
            if response.status_code != 200:
                print("[ERROR] Backend not responding")
                return False
            
            print("  ✓ Backend is healthy")
            print()
            
            # Login first
            print("Authenticating...")
            login_response = client.post(
                f"{base_url}/api/v1/auth/login",
                json={
                    "email": "admin@talent.com",
                    "password": "Secret123!"
                }
            )
            
            if login_response.status_code != 200:
                print(f"[ERROR] Login failed: {login_response.status_code}")
                print(f"  Response: {login_response.text}")
                return False
            
            token_data = login_response.json()
            access_token = token_data.get("access_token")
            print(f"  ✓ Authenticated")
            print()
            
            # Trigger sync with auth token
            print("Triggering sync endpoint...")
            response = client.post(
                f"{base_url}/api/v1/sync/candidates",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code in [200, 202]:
                result = response.json()
                print(f"  Response: {json.dumps(result, indent=2)}")
                print()
                
                if result.get("status") in ["completed", "started", "pending"]:
                    print("✅ Sync triggered successfully!")
                    
                    if result.get("message"):
                        print(f"  Message: {result['message']}")
                    
                    if result.get("stats"):
                        stats = result["stats"]
                        print(f"  Total candidates: {stats.get('total_candidates')}")
                        print(f"  Resumes downloaded: {stats.get('successful')}")
                        print(f"  Resumes failed: {stats.get('failed')}")
                        print(f"  Resumes skipped: {stats.get('skipped')}")
                    
                    return True
            else:
                print(f"[ERROR] Unexpected status: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return False
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(trigger_sync())
    sys.exit(0 if success else 1)
