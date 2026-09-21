#!/usr/bin/env python
"""Test the fixed download_attachment endpoint."""

import os
import json
from pathlib import Path

# Add backend directory to path
os.chdir(Path(__file__).parent)

from app.core.config import settings
from app.integrations.zoho_oauth import ZohoOAuthClient
from app.integrations.zoho_recruit import ZohoRecruitClient
from app.core.crypto import decrypt_value
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models.integration_settings import IntegrationSettings

def test_download():
    """Test downloading a resume attachment."""
    
    print("="*70)
    print("TESTING FIXED DOWNLOAD_ATTACHMENT ENDPOINT")
    print("="*70)
    print()
    
    # Get integration settings from database
    engine = create_engine(settings.database_url)
    
    try:
        with Session(engine) as session:
            # Get Zoho integration
            integration_query = select(IntegrationSettings).where(
                IntegrationSettings.provider == "zoho_recruit"
            )
            integration = session.scalar(integration_query)
            
            if not integration:
                print("❌ No Zoho Recruit integration found")
                return
            
            print(f"✓ Found Zoho integration")
            
            # Get access token
            oauth_client = ZohoOAuthClient()
            access_token = decrypt_value(integration.access_token_encrypted)
            
            print(f"✓ Got access token")
            print()
            
            # Create Zoho client
            zoho_client = ZohoRecruitClient()
            
            # Fetch a candidate to get attachments
            print("Fetching candidates...")
            candidates = list(zoho_client.iter_candidates(access_token, per_page=10))
            
            if not candidates:
                print("❌ No candidates found")
                return
            
            print(f"✓ Found {len(candidates)} candidates")
            print()
            
            # Find a candidate with attachments
            for candidate in candidates[:5]:  # Try first 5
                candidate_id = candidate.get("id")
                candidate_name = candidate.get("Full_Name", "Unknown")
                
                print(f"Checking {candidate_name} (ID: {candidate_id})...")
                
                # Get attachments
                try:
                    attachments = zoho_client.fetch_candidate_attachments(access_token, candidate_id)
                    
                    if not attachments:
                        print(f"  No attachments")
                        continue
                    
                    print(f"  ✓ Found {len(attachments)} attachments")
                    
                    # Try to download first attachment
                    attachment = attachments[0]
                    attachment_id = attachment.get("id")
                    file_name = attachment.get("File_Name", "unknown")
                    expected_size = int(attachment.get("Size", 0))
                    
                    print(f"  Downloading: {file_name} (Expected size: {expected_size} bytes)")
                    print(f"  Attachment ID: {attachment_id}")
                    
                    # Download with fixed endpoint
                    file_content = zoho_client.download_attachment(access_token, attachment_id)
                    
                    actual_size = len(file_content)
                    print(f"  Downloaded: {actual_size} bytes")
                    
                    # Check file signature
                    first_bytes = file_content[:10]
                    is_pdf = first_bytes.startswith(b'%PDF')
                    is_docx = first_bytes.startswith(b'PK')
                    is_doc = first_bytes[:2] in [b'\xd0\xcf', b'\xfd\xff']
                    is_json = first_bytes.startswith(b'{') or first_bytes.startswith(b'[')
                    
                    print(f"  File signature: ", end="")
                    if is_json:
                        print("❌ JSON (ERROR - Still getting metadata!)")
                        # Print JSON content
                        try:
                            data = json.loads(file_content)
                            print(f"  JSON content: {json.dumps(data, indent=2)[:200]}...")
                        except:
                            print(f"  Content: {file_content[:100]}")
                    elif is_pdf:
                        print("✓ PDF")
                    elif is_docx:
                        print("✓ DOCX")
                    elif is_doc:
                        print("✓ DOC")
                    else:
                        print(f"⚠️  Unknown ({first_bytes.hex()[:20]})")
                    
                    # Save test file
                    test_file = Path("test_download.bin")
                    with open(test_file, 'wb') as f:
                        f.write(file_content)
                    print(f"  ✓ Saved to {test_file}")
                    print()
                    
                    # Success!
                    if not is_json:
                        print("="*70)
                        print("✓ SUCCESS! The download_attachment endpoint is now working correctly!")
                        print("✓ Files are being downloaded as binary, not metadata")
                        print("="*70)
                        return
                    
                except Exception as e:
                    print(f"  Error: {e}")
                    continue
            
            print("⚠️  Could not test with valid candidates")
        
    finally:
        engine.dispose()

if __name__ == "__main__":
    test_download()
