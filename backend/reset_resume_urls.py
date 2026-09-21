#!/usr/bin/env python
"""Reset resume URLs in database to trigger re-download."""

import os
from pathlib import Path

# Add backend directory to path
os.chdir(Path(__file__).parent)

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.candidate import Candidate

def reset_resume_urls():
    """Reset all resume URLs in database."""
    
    print("="*70)
    print("RESETTING RESUME URLs IN DATABASE")
    print("="*70)
    
    # Create engine and session
    engine = create_engine(settings.database_url)
    
    try:
        with Session(engine) as session:
            # Count resumes to reset
            count_query = select(Candidate).where(Candidate.resume_url.isnot(None))
            candidates = session.scalars(count_query).all()
            count = len(candidates)
            
            print(f"\nFound {count} candidates with resume URLs")
            
            if count == 0:
                print("No resumes to reset.")
                return
            
            # Reset resume URLs
            update_query = (
                update(Candidate)
                .where(Candidate.resume_url.isnot(None))
                .values(
                    resume_url=None,
                    resume_file_name=None,
                    resume_last_fetched_at=None
                )
            )
            
            session.execute(update_query)
            session.commit()
            
            print(f"✓ Reset {count} resume URLs to NULL")
            
            # Verify
            verify_query = select(Candidate).where(Candidate.resume_url.isnot(None))
            remaining = len(session.scalars(verify_query).all())
            
            print(f"✓ Verification: {remaining} candidates still have resume URLs")
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        raise
    finally:
        engine.dispose()

    print("\n" + "="*70)
    print("READY FOR RE-DOWNLOAD")
    print("="*70)
    print("Resume URLs have been cleared. Next sync will:")
    print("1. Use the fixed download_attachment() endpoint with ?download=true")
    print("2. Download actual PDF/DOC files (not JSON metadata)")
    print("3. Save valid resume files to disk")
    print("="*70)

if __name__ == "__main__":
    reset_resume_urls()
