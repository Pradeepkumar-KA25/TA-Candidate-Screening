#!/usr/bin/env python
"""
Verify all resumes were downloaded and database was updated.
"""

import os
from pathlib import Path
os.chdir(Path(__file__).parent)

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.candidate import Candidate

def verify_downloads():
    """Check that resumes are in database."""
    
    print("=" * 70)
    print("VERIFYING RESUME DOWNLOADS")
    print("=" * 70)
    print()
    
    engine = create_engine(settings.database_url)
    
    with Session(engine) as session:
        # Count total candidates
        total_candidates = session.scalar(select(func.count(Candidate.id)))
        print(f"Total candidates in DB: {total_candidates}")
        
        # Count candidates with resumes
        with_resumes = session.scalar(
            select(func.count(Candidate.id)).where(
                Candidate.resume_url.isnot(None)
            )
        )
        
        print(f"Candidates with resume_url: {with_resumes}")
        print(f"Coverage: {(with_resumes/total_candidates*100):.1f}%")
        print()
        
        # Show samples
        print("Sample resumes:")
        print("-" * 70)
        
        samples = session.query(
            Candidate.full_name,
            Candidate.resume_url,
            Candidate.resume_file_name
        ).filter(
            Candidate.resume_url.isnot(None)
        ).limit(5).all()
        
        for full_name, resume_url, file_name in samples:
            print(f"  {full_name}")
            print(f"    URL: {resume_url}")
            print(f"    File: {file_name}")
            print()
        
        # Check file count on disk
        resume_dir = Path(settings.zoho_resume_storage_path)
        if resume_dir.exists():
            files_on_disk = list(resume_dir.rglob("*.pdf"))
            print(f"Resume files on disk: {len(files_on_disk)}")
        else:
            print("Resume directory doesn't exist")
        
        print()
        print("=" * 70)
        print("✅ VERIFICATION COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    verify_downloads()
