#!/usr/bin/env python
"""Test the multi-endpoint download approach for Zoho attachments."""

import os
from pathlib import Path

os.chdir(Path(__file__).parent)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import logging

from app.core.config import settings
from app.core.crypto import decrypt_value
from app.integrations.zoho_oauth import ZohoOAuthClient
from app.integrations.zoho_recruit import ZohoRecruitClient
from app.models.integration_settings import IntegrationSettings

# Setup logging to see all debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_download_endpoints():
    """Test multiple endpoints for downloading attachments."""
    
    print("="*70)
    print("TESTING MULTI-ENDPOINT DOWNLOAD APPROACH")
    print("="*70)
    print()
    
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
                return False
            
            print(f"✓ Found Zoho integration")
            
            # Get access token
            access_token = decrypt_value(integration.access_token_encrypted)
            print(f"✓ Got access token")
            print()
            
            # Create Zoho client
            zoho_client = ZohoRecruitClient()
            
            # Fetch candidates
            print("Fetching candidates with attachments...")
            candidates = list(zoho_client.iter_candidates(access_token, per_page=50))
            
            if not candidates:
                print("❌ No candidates found")
                return False
            
            print(f"✓ Found {len(candidates)} candidates, checking for attachments...")
            print()
            
            # Find a candidate with attachments
            successful_downloads = 0
            failed_downloads = 0
            
            for candidate in candidates[:20]:  # Check first 20 candidates
                candidate_id = candidate.get("id")
                candidate_name = candidate.get("Full_Name", "Unknown")
                
                try:
                    attachments = zoho_client.fetch_candidate_attachments(access_token, candidate_id)
                    
                    if not attachments:
                        continue
                    
                    # Try to download first attachment
                    attachment = attachments[0]
                    attachment_id = attachment.get("id")
                    file_name = attachment.get("File_Name", "unknown")
                    
                    print(f"Testing download for {candidate_name}")
                    print(f"  Attachment: {file_name}")
                    print(f"  Attachment ID: {attachment_id}")
                    
                    # This will try all endpoints
                    file_content = zoho_client.download_attachment(access_token, attachment_id)
                    
                    actual_size = len(file_content)
                    first_bytes = file_content[:10]
                    
                    is_pdf = first_bytes.startswith(b'%PDF')
                    is_docx = first_bytes.startswith(b'PK')
                    is_doc = first_bytes[:2] in [b'\xd0\xcf', b'\xfd\xff']
                    
                    if is_pdf or is_docx or is_doc:
                        file_type = "PDF" if is_pdf else ("DOCX" if is_docx else "DOC")
                        print(f"  ✅ Downloaded {actual_size} bytes ({file_type})")
                        successful_downloads += 1
                    else:
                        print(f"  ❌ Downloaded but format unknown: {first_bytes.hex()[:20]}")
                        failed_downloads += 1
                    
                    print()
                    
                    # Stop after first successful download
                    if successful_downloads > 0:
                        break
                        
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    failed_downloads += 1
                    print()
            
            print("="*70)
            print(f"Results: {successful_downloads} successful, {failed_downloads} failed")
            print("="*70)
            
            return successful_downloads > 0
        
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = test_download_endpoints()
    exit(0 if success else 1)
