#!/usr/bin/env python
"""Test different download endpoints with file_id."""

import httpx
import json
import sys
import os

def test_download_endpoints():
    """Test various download endpoint patterns."""
    print("ZOHO DOWNLOAD ENDPOINT TESTING")
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
    
    # Get attachment with file_id
    with httpx.Client(timeout=30) as client:
        response = client.get(base_url + "/Candidates?per_page=10", headers=headers)
        candidates = response.json().get("data", [])
        
        for candidate in candidates:
            candidate_id = candidate.get("id")
            
            response = client.get(
                base_url + "/Candidates/" + str(candidate_id) + "/Attachments",
                headers=headers
            )
            
            attachments = response.json().get("data", [])
            if attachments:
                attachment = attachments[0]
                attachment_id = attachment.get("id")
                file_id = attachment.get("$file_id")
                file_name = attachment.get("File_Name")
                size = attachment.get("Size")
                
                print("Test Attachment:")
                print("  File Name: " + file_name)
                print("  Attachment ID: " + str(attachment_id))
                print("  File ID ($file_id): " + str(file_id))
                print("  Expected Size: " + str(size) + " bytes")
                print()
                print("=" * 70)
                print("Testing different endpoint patterns:")
                print("=" * 70)
                print()
                
                # Test different endpoints
                test_endpoints = [
                    ("Using attachment ID (current)", base_url + "/Attachments/" + str(attachment_id)),
                    ("Using file_id directly", base_url + "/Attachments/" + str(file_id)),
                    ("File endpoint with attachment ID", base_url + "/File/" + str(attachment_id)),
                    ("File endpoint with file_id", base_url + "/File/" + str(file_id)),
                    ("Download with attachment ID", base_url + "/Attachments/" + str(attachment_id) + "/download"),
                    ("Download with file_id", base_url + "/Attachments/" + str(file_id) + "/download"),
                ]
                
                for label, endpoint in test_endpoints:
                    print("Testing: " + label)
                    print("  Endpoint: " + endpoint)
                    
                    try:
                        response = client.get(endpoint, headers=headers)
                        
                        print("  HTTP Status: " + str(response.status_code))
                        content_type = response.headers.get('content-type', 'not set')
                        print("  Content-Type: " + content_type)
                        print("  Response Size: " + str(len(response.content)) + " bytes")
                        
                        # Check response type
                        first_bytes = response.content[:10] if response.content else b''
                        
                        if first_bytes.startswith(b'%PDF'):
                            print("  RESULT: [SUCCESS] PDF BINARY DETECTED!")
                            return True
                        elif first_bytes.startswith(b'PK'):
                            print("  RESULT: [SUCCESS] DOCX/ZIP BINARY DETECTED!")
                            return True
                        elif first_bytes[:2] in [b'\xd0\xcf']:
                            print("  RESULT: [SUCCESS] DOC BINARY DETECTED!")
                            return True
                        elif first_bytes.startswith(b'{'):
                            print("  RESULT: [METADATA] JSON response")
                        elif response.status_code == 404:
                            print("  RESULT: [NOT FOUND] Endpoint doesn't exist")
                        elif response.status_code == 403:
                            print("  RESULT: [FORBIDDEN] Access denied")
                        else:
                            print("  RESULT: [UNKNOWN] First bytes: " + first_bytes.hex()[:20])
                        
                    except Exception as e:
                        print("  ERROR: " + str(e)[:100])
                    
                    print()
                
                return False
    
    return False

if __name__ == "__main__":
    success = test_download_endpoints()
    sys.exit(0 if success else 1)
