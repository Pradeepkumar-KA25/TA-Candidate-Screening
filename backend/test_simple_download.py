#!/usr/bin/env python
"""Test simple download with logging."""

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

def test_simple_download():
    """Test downloading a single resume."""
    
    print("=" * 70)
    print("SIMPLE RESUME DOWNLOAD TEST")
    print("=" * 70)
    print()
    
    engine = create_engine(settings.database_url)
    
    try:
        with Session(engine) as session:
            # Get credentials
            print("Getting credentials from database...")
            integration = session.scalar(
                select(IntegrationSettings).where(
                    IntegrationSettings.provider == "zoho_recruit"
                )
            )
            
            if not integration:
                print("[ERROR] No Zoho integration found")
                return False
            
            access_token = decrypt_value(integration.access_token_encrypted)
            print("[OK] Got credentials")
            print()
            
            # Get first candidate
            print("Getting first candidate...")
            candidate = session.scalar(select(Candidate).limit(1))
            
            if not candidate:
                print("[ERROR] No candidates found")
                return False
            
            print(f"[OK] Found: {candidate.full_name}")
            print(f"     Zoho ID: {candidate.zoho_candidate_id}")
            print()
            
            # Get attachments for this candidate
            print("Fetching attachments from Zoho...")
            
            base_url = "https://recruit.zoho.in/recruit/v2"
            headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
            
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    base_url + f"/Candidates/{candidate.zoho_candidate_id}/Attachments",
                    headers=headers
                )
                
                if response.status_code != 200:
                    print(f"[ERROR] Failed to get attachments: HTTP {response.status_code}")
                    return False
                
                attachments = response.json().get('data', [])
                print(f"[OK] Found {len(attachments)} attachment(s)")
                print()
                
                if not attachments:
                    print("[INFO] No attachments to download")
                    return True
                
                # Try to download first attachment
                attachment = attachments[0]
                attachment_id = attachment.get('id')
                file_name = attachment.get('File_Name', 'resume')
                file_size = attachment.get('Size', 'unknown')
                
                print(f"Testing download: {file_name} ({file_size} bytes)")
                print(f"Attachment ID: {attachment_id}")
                print()
                
                # Try direct attachment endpoint
                print("Attempting download from /Attachments/{id} endpoint...")
                response = client.get(
                    base_url + f"/Attachments/{attachment_id}",
                    headers=headers,
                    follow_redirects=True
                )
                
                print(f"Status: HTTP {response.status_code}")
                print(f"Content size: {len(response.content)} bytes")
                
                if response.content:
                    first_bytes = response.content[:20]
                    print(f"First bytes: {first_bytes[:10]}")
                    
                    # Check if binary
                    if first_bytes.startswith(b'%PDF'):
                        print("[OK] PDF file detected!")
                        return True
                    elif first_bytes.startswith(b'PK'):
                        print("[OK] DOCX file detected!")
                        return True
                    elif first_bytes.startswith(b'{'):
                        print("[ERROR] JSON metadata returned (not binary)")
                        print(f"Content: {response.content.decode()[:200]}")
                        return False
                    else:
                        print(f"[WARNING] Unknown format")
                        print(f"Content type header: {response.headers.get('content-type')}")
                        return False
                else:
                    print("[ERROR] No content returned")
                    return False
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_download()
    sys.exit(0 if success else 1)
