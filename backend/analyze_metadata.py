#!/usr/bin/env python
"""Extract and analyze Zoho attachment metadata."""

import httpx
import json
import sys
import os

def analyze_metadata():
    """Get and analyze attachment metadata."""
    print("ZOHO ATTACHMENT METADATA ANALYSIS")
    print("=" * 70)
    print()
    
    # Get token from environment
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")
    if not access_token:
        print("[ERROR] ZOHO_ACCESS_TOKEN not set")
        return False
    
    base_url = "https://recruit.zoho.in/recruit/v2"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    
    print("[OK] Using access token from environment")
    print()
    
    # Get candidates
    print("Fetching candidate with attachments...")
    with httpx.Client(timeout=30) as client:
        response = client.get(
            base_url + "/Candidates?per_page=10",
            headers=headers
        )
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
                    print("[OK] Found candidate: " + candidate_name)
                    attachment = attachments[0]
                    attachment_id = attachment.get("id")
                    
                    print()
                    print("Fetching metadata for attachment: " + attachment.get("File_Name", "unknown"))
                    print()
                    
                    # Get metadata
                    response = client.get(
                        base_url + "/Attachments/" + str(attachment_id),
                        headers=headers
                    )
                    
                    metadata = response.json().get("data", {}) if isinstance(response.json().get("data"), dict) else {}
                    
                    print("Attachment Metadata:")
                    print("-" * 70)
                    for key, value in sorted(metadata.items()):
                        # Truncate long values
                        value_str = str(value)
                        if len(value_str) > 100:
                            value_str = value_str[:100] + "..."
                        print(key + ": " + value_str)
                    
                    print()
                    print("=" * 70)
                    print("ANALYSIS:")
                    print("=" * 70)
                    
                    # Look for download-related fields
                    download_fields = ['file_url', 'download_url', 'download_link', 'url', 'link', '$file_url']
                    
                    found_url = False
                    for field in download_fields:
                        if field in metadata and metadata[field]:
                            print("[FOUND] " + field + ": " + str(metadata[field])[:80])
                            found_url = True
                    
                    if not found_url:
                        print("[NOTE] No download URL field found in metadata")
                        print("[NOTE] Available fields: " + ", ".join(metadata.keys()))
                    
                    # Check for nested data
                    print()
                    print("Checking for nested structures...")
                    for key, value in metadata.items():
                        if isinstance(value, dict):
                            print("[NESTED] " + key + " (object): " + str(list(value.keys())))
                        elif isinstance(value, list):
                            print("[NESTED] " + key + " (array): " + str(len(value)) + " items")
                    
                    return True
    
    return False

if __name__ == "__main__":
    success = analyze_metadata()
    sys.exit(0 if success else 1)
