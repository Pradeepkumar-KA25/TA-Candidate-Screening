#!/usr/bin/env python
"""
Test the FIXED download_attachment with candidate_id parameter.
"""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.crypto import decrypt_value
from app.models.candidate import Candidate
from app.models.integration_settings import IntegrationSettings
from app.integrations.zoho_recruit import ZohoRecruitClient

def test_fixed_download():
    """Test the fixed download_attachment method."""
    
    print("=" * 70)
    print("TESTING FIXED DOWNLOAD_ATTACHMENT")
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
            
            access_token = decrypt_value(integration.access_token_encrypted)
            
            # Get first candidate
            candidate = session.scalar(select(Candidate).limit(1))
            
            if not candidate or not candidate.zoho_candidate_id:
                print("[ERROR] No candidates found")
                return False
            
            print(f"Candidate: {candidate.full_name}")
            print(f"Zoho ID: {candidate.zoho_candidate_id}")
            print()
            
            # Initialize services
            recruit_client = ZohoRecruitClient()
            
            # Get attachments
            print("Fetching attachments...")
            attachments = recruit_client.fetch_candidate_attachments(
                access_token=access_token,
                candidate_id=candidate.zoho_candidate_id
            )
            
            if not attachments:
                print("[ERROR] No attachments found")
                return False
            
            attachment = attachments[0]
            attachment_id = attachment.get('id')
            file_name = attachment.get('File_Name', 'file')
            
            print(f"Found: {file_name} (ID: {attachment_id})")
            print()
            
            # Test FIXED download_attachment
            print("Downloading attachment with FIXED endpoint...")
            print(f"  Endpoint: /recruit/v2/Candidates/{candidate.zoho_candidate_id}/Attachments/{attachment_id}")
            print()
            
            try:
                file_content = recruit_client.download_attachment(
                    access_token=access_token,
                    candidate_id=candidate.zoho_candidate_id,
                    attachment_id=attachment_id
                )
                
                print(f"✅ Download successful!")
                print(f"  File size: {len(file_content)} bytes")
                
                # Check file signature
                first_bytes = file_content[:4]
                if first_bytes.startswith(b'%PDF'):
                    print(f"  File type: PDF ✓")
                elif first_bytes.startswith(b'PK'):
                    print(f"  File type: DOCX/ZIP ✓")
                else:
                    print(f"  File type: Unknown (first bytes: {first_bytes})")
                
                print()
                print("=" * 70)
                print("✅✅✅ SUCCESS! DOWNLOAD IS WORKING!")
                print("=" * 70)
                return True
                
            except Exception as e:
                print(f"❌ Download failed: {str(e)}")
                return False
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fixed_download()
    sys.exit(0 if success else 1)
