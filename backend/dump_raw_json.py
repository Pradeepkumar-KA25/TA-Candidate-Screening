#!/usr/bin/env python
"""Dump raw Zoho attachment JSON response."""

import httpx
import json
import sys
import os

def dump_raw():
    """Dump raw JSON response."""
    print("ZOHO ATTACHMENT RAW JSON DUMP")
    print("=" * 70)
    print()
    
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")
    if not access_token:
        print("[ERROR] ZOHO_ACCESS_TOKEN not set")
        return False
    
    base_url = "https://recruit.zoho.in/recruit/v2"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    
    print("[OK] Connected")
    print()
    
    # Get candidates
    with httpx.Client(timeout=30) as client:
        response = client.get(base_url + "/Candidates?per_page=10", headers=headers)
        candidates = response.json().get("data", [])
        
        # Find candidate with attachments
        for candidate in candidates:
            candidate_id = candidate.get("id")
            candidate_name = candidate.get("Full_Name", "Unknown")
            
            response = client.get(
                base_url + "/Candidates/" + str(candidate_id) + "/Attachments",
                headers=headers
            )
            
            if response.status_code == 200:
                attachments = response.json().get("data", [])
                if attachments:
                    print("Candidate: " + candidate_name)
                    print()
                    
                    attachment = attachments[0]
                    print("FULL ATTACHMENT LIST ITEM:")
                    print("-" * 70)
                    print(json.dumps(attachment, indent=2))
                    print()
                    print("-" * 70)
                    print()
                    
                    # Now get the attachment details
                    attachment_id = attachment.get("id")
                    print("Getting details for attachment ID: " + str(attachment_id))
                    print()
                    
                    response = client.get(
                        base_url + "/Attachments/" + str(attachment_id),
                        headers=headers
                    )
                    
                    print("HTTP Status: " + str(response.status_code))
                    print("Content-Type: " + response.headers.get('content-type', 'not set'))
                    print()
                    print("FULL RESPONSE:")
                    print("-" * 70)
                    try:
                        data = response.json()
                        print(json.dumps(data, indent=2))
                    except:
                        print("Could not parse as JSON. Raw content:")
                        print(response.text[:500])
                    print("-" * 70)
                    
                    return True
    
    return False

if __name__ == "__main__":
    success = dump_raw()
    sys.exit(0 if success else 1)
