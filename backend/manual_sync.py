#!/usr/bin/env python
"""Manually trigger a sync to re-download resumes with fixed endpoint."""

import os
import sys
from pathlib import Path
from uuid import UUID

# Add backend directory to path
os.chdir(Path(__file__).parent)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.repositories.sync_log_repository import SyncLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.integration_settings_repository import IntegrationSettingsRepository
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.normalization_rule_repository import NormalizationRuleRepository
from app.repositories.duplicate_review_repository import DuplicateReviewRepository
from app.services.sync_service import SyncService
from app.services.normalization_service import NormalizationService
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.services.resume_fetch_service import ResumeFetchService

def trigger_sync():
    """Manually trigger sync to re-download resumes."""
    
    print("="*70)
    print("TRIGGERING MANUAL SYNC FOR RESUME RE-DOWNLOAD")
    print("="*70)
    
    # Create engine and session
    engine = create_engine(settings.database_url)
    
    try:
        with Session(engine) as session:
            # Get a recruiter user for the sync
            recruiter_query = select(User).where(User.role == "Recruiter")
            recruiter = session.scalar(recruiter_query)
            
            if not recruiter:
                # If no recruiter, try admin
                admin_query = select(User).where(User.role == "Admin")
                recruiter = session.scalar(admin_query)
            
            if not recruiter:
                print("âŒ No Recruiter or Admin user found in database")
                print("Cannot trigger sync without a user context")
                return
            
            print(f"âœ“ Found user: {recruiter.email} ({recruiter.role})")
            print()
            
            # Initialize repositories
            sync_log_repo = SyncLogRepository(session)
            candidate_repo = CandidateRepository(session)
            integration_repo = IntegrationSettingsRepository(session)
            activity_log_repo = ActivityLogRepository(session)
            normalization_rule_repo = NormalizationRuleRepository(session)
            duplicate_review_repo = DuplicateReviewRepository(session)
            
            # Initialize services
            normalization_service = NormalizationService(repository=normalization_rule_repo)
            duplicate_detection_service = DuplicateDetectionService(candidate_repo, duplicate_review_repo)
            resume_fetch_service = ResumeFetchService(candidate_repo)
            
            sync_service = SyncService(
                sync_log_repository=sync_log_repo,
                candidate_repository=candidate_repo,
                integration_settings_repository=integration_repo,
                activity_log_repository=activity_log_repo,
                normalization_service=normalization_service,
                duplicate_detection_service=duplicate_detection_service,
                resume_fetch_service=resume_fetch_service,
            )
            
            # Start sync
            print("Starting sync...")
            try:
                trigger_response = sync_service.start_sync(recruiter.id)
                sync_id = trigger_response.sync_id
                print(f"âœ“ Sync started with ID: {sync_id}")
                print()
                
                # Run the sync
                print("Running sync (downloading resumes)...")
                print("This may take several minutes...")
                print()
                
                sync_service.run_sync(sync_id)
                
                # Get status
                status = sync_service.get_sync_status(sync_id)
                print()
                print("="*70)
                print(f"Sync Status: {status.status}")
                print(f"Total Candidates: {status.total_candidates}")
                print(f"Newly Added: {status.newly_added}")
                print(f"Updated: {status.updated}")
                print(f"Duplicates Detected: {status.duplicates_detected}")
                print(f"Errors: {status.errors}")
                if status.error_message:
                    print(f"Error Details: {status.error_message}")
                print("="*70)
                
            except Exception as e:
                print(f"âŒ Sync failed: {e}")
                raise
        
    finally:
        engine.dispose()

    print("\n" + "="*70)
    print("SYNC COMPLETE")
    print("="*70)
    print("Resume files have been re-downloaded with the fixed endpoint.")
    print("Run the following command to verify:")
    print("  python check_resumes_summary.py")
    print("="*70)

if __name__ == "__main__":
    trigger_sync()

