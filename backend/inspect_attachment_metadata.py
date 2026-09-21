#!/usr/bin/env python
"""Inspect attachment metadata for download links."""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

import httpx
import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.candidate import Candidate
from app.models.integration_settings import IntegrationSettings
from app.core.crypto import decrypt_value

def inspect_metadata():
    """Check attachment metadata for download info."""
    
    print("=" * 70)
    print("INSPECTING ATTACHMENT METADATA")
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
            
            if not candidate or not candidate.zoho_candidate_id:
                print("[ERROR] No candidates found")
                return False
            
            print(f"Candidate: {candidate.full_name}")
            print()
            
            base_url = "https://recruit.zoho.in/recruit/v2"
            headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
            
            with httpx.Client(timeout=30) as client:
                # Get attachments
                response = client.get(
                    base_url + f"/Candidates/{candidate.zoho_candidate_id}/Attachments",
                    headers=headers
                )
                
                data = response.json()
                attachments = data.get('data', [])
                
                if not attachments:
                    print("[ERROR] No attachments")
                    return False
                
                attachment = attachments[0]
                
                print("Attachment Metadata:")
                print(json.dumps(attachment, indent=2))
                print()
                
                # Check for specific fields that might help
                print("Checking for useful fields...")
                keys_to_check = ['download_url', 'Download_Url', 'file_url', 'File_Url', 'attachment_url', 'Attachment_Url', 'url', 'Url', 'file_id', 'File_Id', 'content_url', 'Content_Url']
                
                found_useful = False
                for key in keys_to_check:
                    if key in attachment:
                        print(f"  Found: {key} = {attachment[key]}")
                        found_useful = True
                
                if not found_useful:
                    print("  No obvious download URL found")
                
                print()
                print("All available fields in attachment object:")
                for key in attachment.keys():
                    value = attachment[key]
                    if isinstance(value, (str, int, float, bool)):
                        print(f"  - {key}: {str(value)[:80]}")
                    else:
                        print(f"  - {key}: {type(value).__name__}")
                
                return True
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = inspect_metadata()
    sys.exit(0 if success else 1)
