#!/usr/bin/env python
"""Test Zoho tokens directly from input - NOT from database."""

import httpx

def test_provided_tokens():
    """Test the exact tokens provided by user."""
    
    # Exact tokens provided
    access_token = "1000.0287eee2d7787850a27791b6b811bc20.f23fba24c17c53aee04e3ac7ee4f958a"
    refresh_token = "1000.016538f89cf868d52ec10a5b687e5754.938160967bfaf48393a18f82bb3c659c"
    client_id = "1000.WA5TEPHE77PLKH4QFWL1NV044OCK7P"
    client_secret = "50686efc31975c713dc65004087e17ee56a7e802e7"
    
    print("=" * 70)
    print("DIRECT TOKEN TEST (NOT FROM DATABASE)")
    print("=" * 70)
    print()
    print("Using provided tokens directly:")
    print("  Access Token: " + access_token[:40] + "...")
    print("  Refresh Token: " + refresh_token[:40] + "...")
    print("  Client ID: " + client_id[:40] + "...")
    print("  Client Secret: " + client_secret[:40] + "...")
    print()
    print("=" * 70)
    print("TEST 1: Fetch Candidates")
    print("=" * 70)
    print()
    
    base_url = "https://recruit.zoho.in/recruit/v2"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                base_url + "/Candidates?per_page=5",
                headers=headers
            )
            
            print("HTTP Status: " + str(response.status_code))
            print("Content-Type: " + response.headers.get('content-type', 'unknown'))
            print()
            
            if response.status_code == 200:
                print("[SUCCESS] Token is VALID and WORKING!")
                print()
                
                data = response.json()
                candidates = data.get('data', [])
                
                print("Total Candidates Retrieved: " + str(len(candidates)))
                print()
                
                if candidates:
                    print("Sample Candidates:")
                    print("-" * 70)
                    for i, cand in enumerate(candidates[:3], 1):
                        print("Candidate " + str(i) + ":")
                        print("  Name: " + cand.get('Full_Name', 'N/A'))
                        print("  Email: " + cand.get('Email', 'N/A'))
                        print("  ID: " + str(cand.get('id', 'N/A')))
                        print()
                    
                    print()
                    print("=" * 70)
                    print("TEST 2: Test Attachment Download Permission")
                    print("=" * 70)
                    print()
                    
                    # Try to get attachments and download
                    test_candidate = candidates[0]
                    candidate_id = test_candidate.get('id')
                    candidate_name = test_candidate.get('Full_Name', 'Unknown')
                    
                    print("Testing with: " + candidate_name)
                    print()
                    
                    # Get attachments
                    response = client.get(
                        base_url + f"/Candidates/{candidate_id}/Attachments",
                        headers=headers
                    )
                    
                    attachments = response.json().get('data', [])
                    
                    if attachments:
                        print("Attachments found: " + str(len(attachments)))
                        attachment = attachments[0]
                        attachment_id = attachment.get('id')
                        file_name = attachment.get('File_Name', 'unknown')
                        file_size = attachment.get('Size', '?')
                        
                        print("  File: " + file_name)
                        print("  Size: " + str(file_size) + " bytes")
                        print("  ID: " + str(attachment_id))
                        print()
                        
                        # Test download
                        print("Testing download endpoint...")
                        response = client.get(
                            base_url + f"/Attachments/{attachment_id}",
                            headers=headers,
                            follow_redirects=False
                        )
                        
                        print("HTTP Status: " + str(response.status_code))
                        print("Content-Type: " + response.headers.get('content-type', 'unknown')[:50])
                        print("Response Size: " + str(len(response.content)) + " bytes")
                        print()
                        
                        first_bytes = response.content[:10] if response.content else b''
                        
                        if first_bytes.startswith(b'%PDF'):
                            print("[SUCCESS] PDF BINARY FILE DETECTED!")
                            print("Download is working!")
                            return True
                        elif first_bytes.startswith(b'PK'):
                            print("[SUCCESS] DOCX/ZIP FILE DETECTED!")
                            print("Download is working!")
                            return True
                        elif response.status_code == 302:
                            location = response.headers.get('location', '')
                            print("Redirect to: " + location[:80])
                            if 'IAMSecurityError' in location:
                                print("[ISSUE] IAM Security Error - Permission denied for download")
                                print("Action: Ask Zoho admin to enable 'Attachments.Download' scope")
                                return False
                            else:
                                print("[INFO] Redirect detected (might need to follow)")
                                return False
                        elif first_bytes.startswith(b'{'):
                            print("[INFO] JSON Response (metadata, not binary)")
                            print("Token can read metadata but might not have download permission yet")
                            return False
                        else:
                            print("[UNKNOWN] First bytes: " + first_bytes.hex()[:20])
                            return False
                    else:
                        print("[INFO] No attachments found for test candidate")
                        print("Token is working but no files to test download")
                        return True
                        
            elif response.status_code == 401:
                print("[ERROR] INVALID TOKEN")
                try:
                    error = response.json()
                    print("Error: " + error.get('message', 'unknown'))
                except:
                    pass
                print()
                print("The provided access token is NOT valid")
                print("Action: Ask Zoho admin to regenerate tokens")
                return False
                
            else:
                print("[ERROR] HTTP " + str(response.status_code))
                print("Response: " + response.text[:300])
                return False
                
    except Exception as e:
        print("[ERROR] Connection failed: " + str(e))
        return False

if __name__ == "__main__":
    success = test_provided_tokens()
    print()
    print("=" * 70)
    if success:
        print("RESULT: Tokens are WORKING!")
    else:
        print("RESULT: Tokens are NOT working or have permission issues")
    print("=" * 70)
    exit(0 if success else 1)
