#!/usr/bin/env python
"""
Test with attachment_id instead of file_id - maybe that's our mistake!
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

def test_with_attachment_id():
    """Test download using attachment_id instead of file_id."""
    
    print("=" * 70)
    print("TESTING WITH ATTACHMENT_ID (NOT file_id)")
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
                attachment_id = attachment.get('id')  # ← USE THIS, NOT $file_id
                file_id = attachment.get('$file_id')
                candidate_id = candidate.zoho_candidate_id
                
                print(f"File: {attachment.get('File_Name')}")
                print(f"Candidate ID: {candidate_id}")
                print(f"Attachment ID: {attachment_id}")
                print(f"File ID: {file_id}")
                print()
                
                endpoints_to_test = [
                    ("v2 with attachment_id", base_url + f"/Attachments/{attachment_id}"),
                    ("v2 with attachment_id + download", base_url + f"/Attachments/{attachment_id}?download=true"),
                    ("With candidate & attachment", base_url + f"/Candidates/{candidate_id}/Attachments/{attachment_id}"),
                    ("Direct download API with attachment_id", f"https://recruit.zoho.in/recruit/api/attachment/download/{attachment_id}"),
                    ("Records attachment endpoint", base_url + f"/records/Attachments/{attachment_id}/download"),
                ]
                
                for name, endpoint in endpoints_to_test:
                    print(f"Testing: {name}")
                    print(f"  Endpoint: {endpoint}")
                    
                    try:
                        response = client.get(endpoint, headers=headers, follow_redirects=True, timeout=10)
                        
                        first_bytes = response.content[:10] if response.content else b''
                        is_binary = first_bytes.startswith(b'%PDF') or first_bytes.startswith(b'PK')
                        
                        print(f"  Status: HTTP {response.status_code}")
                        print(f"  Size: {len(response.content)}")
                        print(f"  First bytes: {first_bytes}")
                        print(f"  Is Binary: {is_binary}")
                        
                        if is_binary:
                            print(f"  ✅✅✅ SUCCESS! This endpoint works!")
                            print()
                            return True
                        elif response.status_code == 302:
                            print(f"  Redirect to: {response.headers.get('location')}")
                        
                    except Exception as e:
                        print(f"  Error: {str(e)}")
                    
                    print()
                
                return False
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_with_attachment_id()
