#!/usr/bin/env python
"""
Monitor sync progress.
"""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

import httpx
import time
import json

def monitor_sync(sync_id: str):
    """Monitor an active sync."""
    
    print("=" * 70)
    print(f"MONITORING SYNC: {sync_id}")
    print("=" * 70)
    print()
    
    base_url = "http://localhost:8000"
    
    try:
        with httpx.Client(timeout=30) as client:
            # Login first to get token
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
                return False
            
            token_data = login_response.json()
            access_token = token_data.get("access_token")
            print("  ✓ Authenticated")
            print()
            
            # Monitor sync
            headers = {"Authorization": f"Bearer {access_token}"}
            max_checks = 60  # Check for up to 60 * 10 = 600 seconds = 10 minutes
            check_count = 0
            
            while check_count < max_checks:
                response = client.get(
                    f"{base_url}/api/v1/sync/{sync_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    print(f"[ERROR] Failed to get sync status: {response.status_code}")
                    return False
                
                status_data = response.json()
                status = status_data.get("status", "unknown")
                
                print(f"[{check_count+1}] Status: {status}")
                print(f"    Candidates processed: {status_data.get('candidates_processed', 0)}")
                print(f"    Resumes downloaded: {status_data.get('resumes_downloaded', 0)}")
                print(f"    Candidates failed: {status_data.get('candidates_failed', 0)}")
                print(f"    Duration: {status_data.get('sync_duration_seconds', 0):.1f}s")
                
                if status == "completed":
                    print()
                    print("=" * 70)
                    print("✅ SYNC COMPLETED!")
                    print("=" * 70)
                    print()
                    print("Summary:")
                    summary = client.get(
                        f"{base_url}/api/v1/sync/{sync_id}/summary",
                        headers=headers
                    )
                    if summary.status_code == 200:
                        summary_data = summary.json()
                        print(json.dumps(summary_data, indent=2))
                    return True
                
                elif status == "failed":
                    print()
                    print("=" * 70)
                    print("❌ SYNC FAILED")
                    print("=" * 70)
                    
                    if status_data.get("error_message"):
                        print(f"Error: {status_data['error_message']}")
                    
                    return False
                
                check_count += 1
                if check_count < max_checks:
                    print()
                    time.sleep(10)  # Wait 10 seconds between checks
            
            print()
            print("[ERROR] Sync timed out after 600 seconds")
            return False
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sync_id = sys.argv[1] if len(sys.argv) > 1 else "05bbb98f-7306-41d6-b9d1-3eb6bd1de4dd"
    
    print(f"Using sync_id: {sync_id}")
    print()
    
    success = monitor_sync(sync_id)
    sys.exit(0 if success else 1)
