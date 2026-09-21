#!/usr/bin/env python
"""Trigger sync by directly calling the resume service."""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

from app.integrations.zoho_oauth import ZohoOAuthClient
from app.integrations.zoho_recruit import ZohoRecruitClient
from app.services.resume_fetch_service import ResumeFetchService
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.candidate import Candidate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trigger_resume_downloads():
    """Download resumes for all candidates with attachments."""
    
    print("=" * 70)
    print("DOWNLOADING RESUMES FROM ZOHO")
    print("=" * 70)
    print()
    
    try:
        # Initialize services
        print("Initializing services...")
        oauth_client = ZohoOAuthClient()
        recruit_client = ZohoRecruitClient(oauth_client=oauth_client)
        resume_service = ResumeFetchService()
        
        print("[OK] Services initialized")
        print()
        
        # Get database connection
        engine = create_engine(settings.database_url)
        
        # Get all candidates
        print("Fetching candidates from database...")
        with Session(engine) as session:
            candidates = session.scalars(
                select(Candidate).order_by(Candidate.id)
            ).all()
            
            total = len(candidates)
            print(f"[OK] Found {total} candidates in database")
            print()
            
            if total == 0:
                print("[WARNING] No candidates in database. Run sync first.")
                return False
            
            # Process first 5 candidates to test
            print("Testing with first 5 candidates...")
            print()
            
            successful = 0
            failed = 0
            
            for idx, candidate in enumerate(candidates[:5], 1):
                try:
                    print(f"[{idx}/5] Processing: {candidate.first_name} {candidate.last_name}")
                    
                    # Fetch candidate from Zoho to get attachment IDs
                    zoho_candidate = recruit_client.get_candidate_with_attachments(candidate.zoho_id)
                    
                    if zoho_candidate and zoho_candidate.get('attachments'):
                        attachments = zoho_candidate['attachments']
                        print(f"        Found {len(attachments)} attachment(s)")
                        
                        # Download first attachment
                        attachment = attachments[0]
                        attachment_id = attachment.get('id')
                        file_name = attachment.get('File_Name', 'resume')
                        
                        print(f"        Downloading: {file_name}")
                        
                        # Download and save
                        success = resume_service.fetch_and_save_resume(
                            candidate=candidate,
                            attachment_id=attachment_id
                        )
                        
                        if success:
                            print(f"        [OK] Resume saved: {candidate.resume_url}")
                            successful += 1
                        else:
                            print(f"        [ERROR] Failed to download")
                            failed += 1
                    else:
                        print(f"        [INFO] No attachments found")
                    
                    print()
                    
                except Exception as e:
                    print(f"        [ERROR] {str(e)[:100]}")
                    failed += 1
                    print()
            
            print("=" * 70)
            print(f"Test Results: {successful} successful, {failed} failed out of 5")
            print("=" * 70)
            print()
            
            if successful > 0:
                print("[SUCCESS] Resume downloads working! Ready to run full sync.")
                return True
            else:
                print("[ERROR] Resume downloads failing. Check logs above.")
                return False
            
    except Exception as e:
        print()
        print("=" * 70)
        print(f"[ERROR] Process failed: {str(e)[:200]}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = trigger_resume_downloads()
    sys.exit(0 if success else 1)
