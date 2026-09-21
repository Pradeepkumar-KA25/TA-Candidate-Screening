#!/usr/bin/env python
"""Quick Zoho attachment endpoint test - no DB dependency."""

import httpx
import json
import sys
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

def quick_test():
    """Quick test of Zoho endpoint."""
    print("ZOHO ATTACHMENT QUICK TEST")
    print("=" * 70)
    print()
    
    # Get token from environment
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")
    if not access_token:
        print("[ERROR] ZOHO_ACCESS_TOKEN not set in environment")
        return False
    
    base_url = "https://recruit.zoho.in/recruit/v2"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    
    print("[OK] Using access token from environment")
    print("Base URL: " + base_url)
    print()
    
    # Step 1: Get candidates
    print("Step 1: Fetching candidates...")
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                base_url + "/Candidates?per_page=10",
                headers=headers
            )
            if response.status_code != 200:
                print("[ERROR] Failed to fetch candidates: " + str(response.status_code))
                print("Response: " + response.text[:200])
                return False
            
            candidates = response.json().get("data", [])
            print("[OK] Got " + str(len(candidates)) + " candidates")
            
            if not candidates:
                print("[ERROR] No candidates returned")
                return False
    except Exception as e:
        print("[ERROR] Failed to fetch candidates: " + str(e))
        return False
    
    # Step 2: Find candidate with attachments
    print("Step 2: Finding candidate with attachments...")
    test_candidate_id = None
    test_attachment_id = None
    test_file_name = None
    
    try:
        with httpx.Client(timeout=30) as client:
            for candidate in candidates:
                candidate_id = candidate.get("id")
                candidate_name = candidate.get("Full_Name", "Unknown")
                
                # Get attachments for this candidate
                response = client.get(
                    base_url + "/Candidates/" + str(candidate_id) + "/Attachments",
                    headers=headers
                )
                
                if response.status_code == 200:
                    attachments = response.json().get("data", [])
                    if attachments:
                        test_candidate_id = candidate_id
                        test_attachment_id = attachments[0].get("id")
                        test_file_name = attachments[0].get("File_Name", "unknown")
                        print("[OK] Found: " + candidate_name)
                        print("  File: " + test_file_name)
                        print("  Attachment ID: " + test_attachment_id)
                        break
        
        if not test_attachment_id:
            print("[ERROR] No attachments found in candidates")
            return False
    except Exception as e:
        print("[ERROR] Failed to find attachments: " + str(e))
        return False
    
    print()
    print("=" * 70)
    print("Step 3: Testing different Accept headers")
    print("=" * 70)
    print()
    
    # Test different headers
    test_cases = [
        ("No Accept header", {}),
        ("Accept: application/octet-stream", {"Accept": "application/octet-stream"}),
        ("Accept: */*", {"Accept": "*/*"}),
        ("Accept: application/pdf", {"Accept": "application/pdf"}),
    ]
    
    best_case = None
    
    try:
        with httpx.Client(timeout=30) as client:
            for case_name, extra_headers in test_cases:
                print("Testing: " + case_name)
                request_headers = {**headers, **extra_headers}
                endpoint = base_url + "/Attachments/" + str(test_attachment_id)
                
                try:
                    response = client.get(endpoint, headers=request_headers)
                    
                    print("  HTTP Status: " + str(response.status_code))
                    print("  Content-Type: " + response.headers.get('content-type', 'not set'))
                    print("  Response Size: " + str(len(response.content)) + " bytes")
                    
                    # Check response type
                    first_bytes = response.content[:10] if response.content else b''
                    
                    # Binary check
                    if first_bytes.startswith(b'%PDF'):
                        print("  RESULT: [PDF] BINARY FILE")
                        best_case = case_name
                        break
                    elif first_bytes.startswith(b'PK'):
                        print("  RESULT: [DOCX/ZIP] BINARY FILE")
                        best_case = case_name
                        break
                    elif first_bytes[:2] in [b'\xd0\xcf']:
                        print("  RESULT: [DOC] BINARY FILE")
                        best_case = case_name
                        break
                    elif first_bytes.startswith(b'{'):
                        print("  RESULT: [JSON] Metadata (not binary)")
                        try:
                            data = json.loads(response.content)
                            keys = []
                            if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                                keys = list(data["data"][0].keys())
                            print("  JSON keys: " + str(keys[:3]))
                        except:
                            pass
                    else:
                        print("  RESULT: [UNKNOWN] First bytes: " + first_bytes.hex())
                    
                    print()
                    
                except Exception as e:
                    print("  ERROR: " + str(e))
                    print()
    except Exception as e:
        print("[ERROR] Test loop failed: " + str(e))
        return False
    
    print("=" * 70)
    if best_case:
        print("[SUCCESS] Working header found: " + best_case)
        return True
    else:
        print("[FAILED] No working header found")
        print("All endpoints returned JSON metadata instead of binary")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
