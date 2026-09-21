#!/usr/bin/env python
"""Clean up corrupted resume files and reset database."""

import shutil
from pathlib import Path

# Directories
resume_dir = Path("uploads/resumes")

print("="*70)
print("CLEANING UP CORRUPTED RESUME FILES")
print("="*70)

if resume_dir.exists():
    # Count files before
    files_before = list(resume_dir.glob("*/resume.*"))
    print(f"\nFound {len(files_before)} corrupted resume files")
    
    # Remove all resume files
    try:
        shutil.rmtree(resume_dir)
        print(f"✓ Deleted {resume_dir}")
    except Exception as e:
        print(f"❌ Error deleting directory: {e}")
        exit(1)
else:
    print(f"Resume directory doesn't exist: {resume_dir}")

# Create empty directory structure
print("\nRecreating directory structure...")
try:
    resume_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created {resume_dir}")
except Exception as e:
    print(f"❌ Error creating directory: {e}")
    exit(1)

print("\n" + "="*70)
print("NEXT STEPS:")
print("="*70)
print("1. Run: python reset_auto_sync_interval.py")
print("2. Wait for next sync cycle (or manually trigger sync)")
print("3. Resume files will be re-downloaded with correct endpoint")
print("4. Run: python check_resumes_summary.py")
print("   to verify files are now valid PDFs/DOCs")
print("="*70)
