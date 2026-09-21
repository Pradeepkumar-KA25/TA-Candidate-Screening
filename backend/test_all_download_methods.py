#!/usr/bin/env python
"""Comprehensive test of multiple Zoho download methods with new token."""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import httpx

from app.core.config import settings
from app.core.crypto import decrypt_value
from app.models.integration_settings import IntegrationSettings

def test_all_download_methods():
    """Test multiple download approaches."""
    
    print("=" * 70)
    print("COMPREHENSIVE DOWNLOAD PERMISSION TEST")
    print("=" * 70)
    print()
    
    engine = create_engine(settings.database_url)
    
    try:
        with Session(engine) as session:
            integration = session.scalar(
                select(IntegrationSettings).where(
                    IntegrationSettings.provider == "zoho_recruit"
                )
            )
            
            if not integration:
                print("[ERROR] No Zoho integration found")
                return False
            
            access_token = decrypt_value(integration.access_token_encrypted)
            base_url = "https://recruit.zoho.in/recruit/v2"
            headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
            
            print("[OK] Using new token from database")
            print()
            
            # Get test candidate and attachment
            with httpx.Client(timeout=30) as client:
                response = client.get(base_url + "/Candidates?per_page=1", headers=headers)
                candidates = response.json().get("data", [])
                
                if not candidates:
                    print("[ERROR] No candidates found")
                    return False
                
                candidate_id = candidates[0].get("id")
                candidate_name = candidates[0].get("Full_Name", "Unknown")
                
                response = client.get(
                    base_url + f"/Candidates/{candidate_id}/Attachments",
                    headers=headers
                )
                
                attachments = response.json().get("data", [])
                if not attachments:
                    print("[ERROR] No attachments found")
                    return False
                
                attachment = attachments[0]
                attachment_id = attachment.get("id")
                file_id = attachment.get("$file_id")
                file_name = attachment.get("File_Name", "unknown")
                
                print("Test File: " + file_name)
                print("Attachment ID: " + str(attachment_id))
                print("File ID: " + str(file_id))
                print()
                print("=" * 70)
                print("Testing 8 different download methods:")
                print("=" * 70)
                print()
                
                # Test different methods
                test_methods = [
                    ("Method 1: /Attachments/{id} with no special headers", 
                     base_url + f"/Attachments/{attachment_id}", 
                     {"Authorization": f"Zoho-oauthtoken {access_token}"}),
                    
                    ("Method 2: /Attachments/{id} with Accept: application/octet-stream",
                     base_url + f"/Attachments/{attachment_id}",
                     {**headers, "Accept": "application/octet-stream"}),
                    
                    ("Method 3: /Attachments/{id}?file=true",
                     base_url + f"/Attachments/{attachment_id}?file=true",
                     headers),
                    
                    ("Method 4: /Attachments/{id}?download=true",
                     base_url + f"/Attachments/{attachment_id}?download=true",
                     headers),
                    
                    ("Method 5: /recruit/api/attachment/download/{id} (old API)",
                     "https://recruit.zoho.in/recruit/api/attachment/download/" + str(attachment_id),
                     headers),
                    
                    ("Method 6: /File/{file_id}",
                     base_url + f"/File/{file_id}",
                     headers),
                    
                    ("Method 7: /recruit/v2/Attachments/{id}?type=file",
                     base_url + f"/Attachments/{attachment_id}?type=file",
                     headers),
                    
                    ("Method 8: Direct with follow redirects",
                     "https://recruit.zoho.in/recruit/api/attachment/download/" + str(attachment_id),
                     headers),
                ]
                
                best_method = None
                
                for method_name, endpoint, method_headers in test_methods:
                    print("Testing: " + method_name)
                    print("  Endpoint: " + endpoint[:80])
                    
                    try:
                        # Try both with and without following redirects
                        follow_redirects = "Direct with follow" in method_name
                        
                        response = client.get(
                            endpoint,
                            headers=method_headers,
                            follow_redirects=follow_redirects
                        )
                        
                        print("  HTTP Status: " + str(response.status_code))
                        
                        first_bytes = response.content[:10] if response.content else b''
                        
                        if first_bytes.startswith(b'%PDF'):
                            print("  RESULT: [SUCCESS] PDF BINARY DETECTED!")
                            best_method = method_name
                            break
                        elif first_bytes.startswith(b'PK'):
                            print("  RESULT: [SUCCESS] DOCX/ZIP BINARY DETECTED!")
                            best_method = method_name
                            break
                        elif first_bytes[:2] in [b'\xd0\xcf']:
                            print("  RESULT: [SUCCESS] DOC BINARY DETECTED!")
                            best_method = method_name
                            break
                        elif response.status_code == 302:
                            location = response.headers.get('location', '')
                            if 'IAMSecurityError' in location:
                                print("  RESULT: [BLOCKED] IAM Security Error - permission denied")
                            else:
                                print("  RESULT: [REDIRECT] " + location[:60])
                        elif first_bytes.startswith(b'{'):
                            print("  RESULT: [METADATA] JSON response (not binary)")
                        else:
                            print("  RESULT: [UNKNOWN] Content-Type: " + response.headers.get('content-type', '?'))
                        
                    except Exception as e:
                        print("  ERROR: " + str(e)[:80])
                    
                    print()
                
                if best_method:
                    print("=" * 70)
                    print("[SUCCESS] Found working method: " + best_method)
                    print("=" * 70)
                    return True
                else:
                    print("=" * 70)
                    print("[FAILED] No method returned binary file")
                    print()
                    print("This suggests the token still lacks necessary permissions.")
                    print("However, try these additional steps:")
                    print("1. Check Zoho admin console: Settings > Security > OAuth tokens")
                    print("2. Verify token status shows 'Active' and includes file permissions")
                    print("3. In Connected Apps, check if 'Attachments' scope is checked")
                    print("4. Ask admin to check API call logs in Zoho for 'permission denied' errors")
                    print("=" * 70)
                    return False
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = test_all_download_methods()
    sys.exit(0 if success else 1)
