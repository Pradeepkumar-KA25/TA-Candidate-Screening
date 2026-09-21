#!/usr/bin/env python
"""Test Zoho base URLs and file patterns."""

import httpx
import json
import sys
import os

def test_base_urls():
    """Test different base URL patterns for file download."""
    print("ZOHO BASE URL PATTERNS TESTING")
    print("=" * 70)
    print()
    
    access_token = os.getenv("ZOHO_ACCESS_TOKEN")
    if not access_token:
        print("[ERROR] ZOHO_ACCESS_TOKEN not set")
        return False
    
    # Get attachment details first
    base_url_v2 = "https://recruit.zoho.in/recruit/v2"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    
    with httpx.Client(timeout=30) as client:
        response = client.get(base_url_v2 + "/Candidates?per_page=1", headers=headers)
        candidates = response.json().get("data", [])
        
        candidate_id = candidates[0].get("id")
        response = client.get(
            base_url_v2 + "/Candidates/" + str(candidate_id) + "/Attachments",
            headers=headers
        )
        
        attachments = response.json().get("data", [])
        if not attachments:
            print("[ERROR] No attachments found")
            return False
        
        attachment = attachments[0]
        attachment_id = attachment.get("id")
        file_id = attachment.get("$file_id")
        file_name = attachment.get("File_Name")
        
        print("Test File: " + file_name)
        print("Attachment ID: " + str(attachment_id))
        print("File ID: " + str(file_id))
        print()
        print("=" * 70)
        print("Testing different base URL patterns:")
        print("=" * 70)
        print()
        
        # Test different base URLs and patterns
        test_patterns = [
            # Different base URLs
            ("V2 Recruiter (current)", base_url_v2 + "/Attachments/" + str(attachment_id)),
            ("V1 API", "https://recruit.zoho.in/recruit/api/json/Attachments?id=" + str(attachment_id) + "&wf=true"),
            
            # File service patterns
            ("File service base", "https://file.zoho.in/file/" + str(file_id)),
            ("File service v2", "https://recruit.zoho.in/file/" + str(file_id)),
            
            # Download patterns
            ("Download link format", "https://recruit.zoho.in/recruit/api/attachment/download/" + str(attachment_id)),
            
            # Raw ID patterns
            ("Raw file download", "https://recruit.zoho.in/recruit/v2/Attachments/" + str(attachment_id) + "?type=original"),
        ]
        
        for label, url in test_patterns:
            print("Testing: " + label)
            print("  URL: " + url)
            
            try:
                response = client.get(url, headers=headers, follow_redirects=True)
                
                print("  HTTP Status: " + str(response.status_code))
                print("  Content-Type: " + response.headers.get('content-type', 'not set')[:50])
                print("  Response Size: " + str(len(response.content)) + " bytes")
                
                first_bytes = response.content[:10] if response.content else b''
                
                if first_bytes.startswith(b'%PDF'):
                    print("  [SUCCESS] PDF BINARY!")
                    return True
                elif first_bytes.startswith(b'PK'):
                    print("  [SUCCESS] DOCX/ZIP BINARY!")
                    return True
                elif first_bytes[:2] in [b'\xd0\xcf']:
                    print("  [SUCCESS] DOC BINARY!")
                    return True
                elif first_bytes.startswith(b'{'):
                    print("  Result: JSON (not binary)")
                elif first_bytes.startswith(b'<'):
                    print("  Result: HTML/XML")
                elif response.status_code in [302, 301]:
                    print("  Result: Redirect")
                    if 'location' in response.headers:
                        print("  Location: " + response.headers['location'][:100])
                elif response.status_code == 404:
                    print("  Result: 404 Not Found")
                elif response.status_code == 403:
                    print("  Result: 403 Forbidden")
                else:
                    print("  Result: Unknown (" + first_bytes.hex()[:20] + ")")
                    
            except Exception as e:
                print("  ERROR: " + str(e)[:100])
            
            print()
        
        return False

if __name__ == "__main__":
    success = test_base_urls()
    sys.exit(0 if success else 1)
