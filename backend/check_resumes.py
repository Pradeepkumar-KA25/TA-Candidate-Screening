#!/usr/bin/env python
"""Diagnostic script to check downloaded resumes."""

from pathlib import Path
import sys

# Check all resumes in the uploads/resumes directory
resume_dir = Path("uploads/resumes")

if not resume_dir.exists():
    print(f"❌ Resume directory not found: {resume_dir}")
    sys.exit(1)

print(f"✓ Resume directory found: {resume_dir}")
print(f"✓ Current directory: {Path.cwd()}")
print()

# Find all resume files
resume_files = list(resume_dir.glob("*/resume.*"))
print(f"Found {len(resume_files)} resume files:")
print()

for resume_file in sorted(resume_files):
    size = resume_file.stat().st_size
    
    # Read first 20 bytes to check file signature
    with open(resume_file, 'rb') as f:
        first_bytes = f.read(20)
    
    hex_sig = first_bytes.hex() if first_bytes else "EMPTY"
    
    # Check file type
    file_type = "UNKNOWN"
    is_valid = False
    
    if first_bytes.startswith(b'%PDF'):
        file_type = "PDF ✓"
        is_valid = True
    elif first_bytes.startswith(b'PK'):
        file_type = "DOCX/ZIP ✓"
        is_valid = True
    elif first_bytes[:2] in [b'\xd0\xcf', b'\xfd\xff']:
        file_type = "DOC/OLE ✓"
        is_valid = True
    elif len(first_bytes) == 0:
        file_type = "EMPTY ❌"
        is_valid = False
    else:
        # Check if it's JSON (error response)
        if first_bytes.startswith(b'{') or first_bytes.startswith(b'['):
            file_type = "JSON ❌"
            is_valid = False
        else:
            file_type = "UNKNOWN"
            is_valid = False
    
    # Format output
    status = "✓" if is_valid else "❌"
    print(f"{status} {str(resume_file)}")
    print(f"   Size: {size} bytes, Type: {file_type}, Sig: {hex_sig[:20]}...")
    print()

# Summary
valid_count = sum(1 for f in resume_files if f.stat().st_size > 0)
empty_count = sum(1 for f in resume_files if f.stat().st_size == 0)

print(f"\n{'='*60}")
print(f"Total files: {len(resume_files)}")
print(f"Valid files: {valid_count}")
print(f"Empty/Invalid files: {empty_count}")
print(f"{'='*60}")

if empty_count > 0:
    print("\n⚠️  WARNING: Some resume files are empty or have invalid format!")
    print("This suggests an issue with the Zoho API download.")
    sys.exit(1)
else:
    print("\n✓ All resume files appear to be valid!")
    sys.exit(0)
