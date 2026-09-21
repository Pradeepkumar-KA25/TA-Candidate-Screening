#!/usr/bin/env python
"""Trigger sync with proper dependency injection."""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

from fastapi import FastAPI
from app.core.dependencies import (
    get_sync_service,
    get_auth_service,
    get_candidate_service,
    get_duplicate_detection_service,
    get_ranking_service,
    get_zoho_oauth_client
)

def trigger_sync_with_dependencies():
    """Trigger sync with proper dependencies."""
    
    print("=" * 70)
    print("TRIGGERING CANDIDATE SYNC WITH DEPENDENCIES")
    print("=" * 70)
    print()
    
    try:
        # Get all dependencies
        print("Initializing services...")
        
        zoho_oauth_client = get_zoho_oauth_client()
        auth_service = get_auth_service()
        candidate_service = get_candidate_service()
        duplicate_detection_service = get_duplicate_detection_service()
        ranking_service = get_ranking_service()
        sync_service = get_sync_service(
            zoho_oauth_client=zoho_oauth_client,
            auth_service=auth_service,
            candidate_service=candidate_service,
            duplicate_detection_service=duplicate_detection_service,
            ranking_service=ranking_service
        )
        
        print("[OK] All services initialized")
        print()
        print("Starting sync...")
        print()
        print("=" * 70)
        
        # Run sync
        result = sync_service.run_sync()
        
        print()
        print("=" * 70)
        print("[SUCCESS] Sync process completed!")
        print("=" * 70)
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print("[ERROR] Sync failed: " + str(e)[:200])
        print("=" * 70)
        return False

if __name__ == "__main__":
    success = trigger_sync_with_dependencies()
    sys.exit(0 if success else 1)
