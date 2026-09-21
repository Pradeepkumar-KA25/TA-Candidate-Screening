#!/usr/bin/env python
"""
Check the actual HTML/error response from Zoho when trying to download.
"""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.crypto import decrypt_value
from app.models.candidate import Candidate
from app.models.integration_settings import IntegrationSettings

def check_error_response():
    """Get the full error response."""
    
    print("=" * 70)
    print("CHECKING ERROR RESPONSE FROM ZOHO")
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
            
            access_token = decrypt_value(integration.access_token_encrypted)
            candidate = session.scalar(select(Candidate).limit(1))
            
            base_url = "https://recruit.zoho.in/recruit/v2"
            headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
            
            with httpx.Client(timeout=30) as client:
                # Get attachment
                response = client.get(
                    base_url + f"/Candidates/{candidate.zoho_candidate_id}/Attachments",
                    headers=headers
                )
                
                attachments = response.json().get('data', [])
                attachment = attachments[0]
                file_id = attachment.get('$file_id')
                
                print(f"File: {attachment.get('File_Name')}")
                print(f"File ID: {file_id}")
                print()
                
                # Test v2 API endpoint
                print("Testing: /recruit/v2/Attachments/{file_id}")
                response = client.get(
                    base_url + f"/Attachments/{file_id}",
                    headers=headers,
                    follow_redirects=True
                )
                
                print(f"Status: HTTP {response.status_code}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                print()
                print("Response:")
                print(response.text[:1000])
                print()
                
                # Test download endpoint
                print("=" * 70)
                print()
                print("Testing: /recruit/api/attachment/download/{file_id}")
                response = client.get(
                    f"https://recruit.zoho.in/recruit/api/attachment/download/{file_id}",
                    headers=headers,
                    follow_redirects=False
                )
                
                print(f"Status: HTTP {response.status_code}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                print(f"Content Size: {len(response.content)}")
                
                if response.status_code == 302:
                    print(f"Redirect to: {response.headers.get('location')}")
                
                print()
                print("Response:")
                print(response.text[:1500])
                
                return True
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_error_response()
