#!/usr/bin/env python
"""Test all possible download endpoints."""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.candidate import Candidate
from app.models.integration_settings import IntegrationSettings
from app.core.crypto import decrypt_value

def test_all_endpoints():
    """Try all possible download endpoints."""
    
    print("=" * 70)
    print("TESTING ALL DOWNLOAD ENDPOINTS")
    print("=" * 70)
    print()
    
    engine = create_engine(settings.database_url)
    
    try:
        with Session(engine) as session:
            # Get credentials
            integration = session.scalar(
                select(IntegrationSettings).where(
                    IntegrationSettings.provider == "zoho_recruit"
                )
            )
            
            if not integration:
                print("[ERROR] No Zoho integration found")
                return False
            
            access_token = decrypt_value(integration.access_token_encrypted)
            
            # Get first candidate
            candidate = session.scalar(select(Candidate).limit(1))
            
            if not candidate or not candidate.zoho_candidate_id:
                print("[ERROR] No candidates with zoho_candidate_id found")
                return False
            
            print(f"Testing: {candidate.full_name}")
            print(f"Candidate Zoho ID: {candidate.zoho_candidate_id}")
            print()
            
            # Get attachments
            base_url = "https://recruit.zoho.in/recruit/v2"
            headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
            
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    base_url + f"/Candidates/{candidate.zoho_candidate_id}/Attachments",
                    headers=headers
                )
                
                attachments = response.json().get('data', [])
                
                if not attachments:
                    print("[ERROR] No attachments found")
                    return False
                
                attachment = attachments[0]
                attachment_id = attachment.get('id')
                file_name = attachment.get('File_Name', 'resume')
                
                print(f"Testing file: {file_name}")
                print(f"Attachment ID: {attachment_id}")
                print()
                
                # All endpoints to try
                endpoints = [
                    ("V2 - /Attachments/{id}", base_url + f"/Attachments/{attachment_id}", {}),
                    ("V2 - /Attachments/{id} with octet-stream", base_url + f"/Attachments/{attachment_id}", {"Accept": "application/octet-stream"}),
                    ("V2 - /Attachments/{id} with */*", base_url + f"/Attachments/{attachment_id}", {"Accept": "*/*"}),
                    ("Download API - /recruit/api/attachment/download/{id}", "https://recruit.zoho.in/recruit/api/attachment/download/" + str(attachment_id), {}),
                    ("Download API - with referer", "https://recruit.zoho.in/recruit/api/attachment/download/" + str(attachment_id), {"Referer": "https://recruit.zoho.in"}),
                    ("Stream endpoint", base_url + f"/Attachments/{attachment_id}?download=true", {}),
                    ("Content endpoint", base_url + f"/Candidates/{candidate.zoho_candidate_id}/Attachments/{attachment_id}/content", {}),
                    ("Direct endpoint", base_url + f"/Attachments/{attachment_id}/download", {}),
                ]
                
                for name, endpoint, extra_headers in endpoints:
                    print(f"Testing: {name}")
                    
                    request_headers = {**headers, **extra_headers}
                    
                    try:
                        response = client.get(endpoint, headers=request_headers, follow_redirects=False)
                        
                        first_bytes = response.content[:10] if response.content else b''
                        content_len = len(response.content) if response.content else 0
                        
                        is_pdf = first_bytes.startswith(b'%PDF')
                        is_docx = first_bytes.startswith(b'PK')
                        is_json = first_bytes.startswith(b'{')
                        
                        status_icon = "✓" if (is_pdf or is_docx) else "✗"
                        
                        print(f"  Status: HTTP {response.status_code}")
                        print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
                        print(f"  Size: {content_len} bytes")
                        print(f"  First bytes: {first_bytes[:10]}")
                        print(f"  Is PDF: {is_pdf}, Is DOCX: {is_docx}, Is JSON: {is_json}")
                        
                        if response.status_code == 302:
                            print(f"  Redirect to: {response.headers.get('location')}")
                        
                        print(f"  Result: {status_icon}")
                        
                        if is_pdf or is_docx:
                            print()
                            print("=" * 70)
                            print(f"[SUCCESS] Found working endpoint: {name}")
                            print("=" * 70)
                            return True
                        
                    except Exception as e:
                        print(f"  Error: {str(e)[:80]}")
                    
                    print()
                
                print("=" * 70)
                print("[NO WORKING ENDPOINT FOUND]")
                print("=" * 70)
                return False
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_all_endpoints()
    sys.exit(0 if success else 1)
