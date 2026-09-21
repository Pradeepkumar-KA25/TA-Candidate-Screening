#!/usr/bin/env python
"""Trigger full candidate sync from Zoho."""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

from app.services.sync_service import SyncService
from app.integrations.zoho_oauth import ZohoOAuthClient

def trigger_sync():
    """Trigger the sync process."""
    
    print("=" * 70)
    print("TRIGGERING FULL CANDIDATE SYNC")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Fetch all candidates from Zoho")
    print("  2. Download resumes for each candidate")
    print("  3. Save to: backend/uploads/resumes/{candidate_id}/resume.{ext}")
    print("  4. Update database with file locations")
    print()
    print("Estimated time: 5-15 minutes (depends on Zoho API response time)")
    print()
    print("Starting sync...")
    print()
    print("=" * 70)
    
    try:
        sync_service = SyncService(zoho_oauth_client=ZohoOAuthClient())
        result = sync_service.run_sync()
        
        print()
        print("=" * 70)
        print("[SUCCESS] Sync completed!")
        print("=" * 70)
        print()
        print("Check backend logs for detailed sync results")
        print("Resume files should now be in: backend/uploads/resumes/")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print("[ERROR] Sync failed: " + str(e))
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = trigger_sync()
    sys.exit(0 if success else 1)
