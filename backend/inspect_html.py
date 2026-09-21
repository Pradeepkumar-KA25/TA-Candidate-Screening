#!/usr/bin/env python
"""Inspect HTML responses from Zoho."""

import httpx
import json
import sys
import os

def inspect_html():
    """Inspect HTML responses."""
    print("INSPECTING HTML RESPONSES FROM ZOHO")
    print("=" * 70)
    print()
    
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")
    if not access_token:
        print("[ERROR] ZOHO_ACCESS_TOKEN not set")
        return False
    
    base_url_v2 = "https://recruit.zoho.in/recruit/v2"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        response = client.get(base_url_v2 + "/Candidates?per_page=1", headers=headers)
        candidates = response.json().get("data", [])
        candidate_id = candidates[0].get("id")
        
        response = client.get(
            base_url_v2 + "/Candidates/" + str(candidate_id) + "/Attachments",
            headers=headers
        )
        
        attachments = response.json().get("data", [])
        attachment = attachments[0]
        attachment_id = attachment.get("id")
        
        print("Testing: https://recruit.zoho.in/recruit/api/attachment/download/" + str(attachment_id))
        print()
        
        # Test without following redirects
        response = client.get(
            "https://recruit.zoho.in/recruit/api/attachment/download/" + str(attachment_id),
            headers=headers
        )
        
        print("HTTP Status: " + str(response.status_code))
        print("Headers:")
        for key, value in list(response.headers.items())[:10]:
            print("  " + key + ": " + str(value)[:100])
        print()
        
        # Check for redirect
        if response.status_code in [301, 302, 303, 307, 308]:
            print("[REDIRECT DETECTED]")
            if 'location' in response.headers:
                print("  Location: " + response.headers['location'])
                print()
                print("Following redirect...")
                response = client.get(response.headers['location'], headers=headers, follow_redirects=True)
                print("Final Status: " + str(response.status_code))
                print("Final Content-Type: " + response.headers.get('content-type', 'not set')[:50])
                print("Final Size: " + str(len(response.content)))
                
                first = response.content[:10]
                if first.startswith(b'%PDF'):
                    print("[SUCCESS] PDF BINARY FOUND!")
                    return True
        
        # Check HTML content
        print("HTML Content (first 1000 chars):")
        print("-" * 70)
        try:
            text = response.content.decode('utf-8', errors='ignore')[:1000]
            print(text)
        except:
            print("[Cannot decode as text]")
        print("-" * 70)

if __name__ == "__main__":
    inspect_html()
