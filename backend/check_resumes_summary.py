#!/usr/bin/env python
"""Diagnostic script to check downloaded resumes - Summary version."""

from pathlib import Path
import sys

# Check all resumes in the uploads/resumes directory
resume_dir = Path("uploads/resumes")

if not resume_dir.exists():
    print(f"❌ Resume directory not found: {resume_dir}")
    sys.exit(1)

print(f"✓ Resume directory found: {resume_dir}")
print()

# Find all resume files
resume_files = list(resume_dir.glob("*/resume.*"))
print(f"Found {len(resume_files)} resume files")
print()

# Check file signatures
valid_files = []
empty_files = []
invalid_files = []
json_files = []

for resume_file in sorted(resume_files):
    size = resume_file.stat().st_size
    
    # Read first 20 bytes to check file signature
    with open(resume_file, 'rb') as f:
        first_bytes = f.read(20)
    
    # Check file type
    if size == 0:
        empty_files.append((resume_file, size))
    elif first_bytes.startswith(b'%PDF'):
        valid_files.append((resume_file, size, 'PDF'))
    elif first_bytes.startswith(b'PK'):
        valid_files.append((resume_file, size, 'DOCX'))
    elif first_bytes[:2] in [b'\xd0\xcf', b'\xfd\xff']:
        valid_files.append((resume_file, size, 'DOC'))
    elif first_bytes.startswith(b'{') or first_bytes.startswith(b'['):
        json_files.append((resume_file, size))
    else:
        invalid_files.append((resume_file, size, first_bytes[:10].hex()))

# Print summary
print(f"{'='*70}")
print(f"RESUME FILE ANALYSIS SUMMARY")
print(f"{'='*70}")
print(f"✓ Valid files: {len(valid_files)}")
print(f"❌ Empty files: {len(empty_files)}")
print(f"❌ JSON files (likely errors): {len(json_files)}")
print(f"❌ Invalid/Unknown format: {len(invalid_files)}")
print(f"{'='*70}")
print()

# Show sample valid files
if valid_files:
    print("Sample valid files:")
    for f, size, ftype in valid_files[:3]:
        print(f"  ✓ {str(f)} - {size} bytes ({ftype})")
    if len(valid_files) > 3:
        print(f"  ... and {len(valid_files) - 3} more")
    print()

# Show empty files
if empty_files:
    print(f"Empty files ({len(empty_files)}):")
    for f, size in empty_files[:5]:
        print(f"  ❌ {str(f)}")
    if len(empty_files) > 5:
        print(f"  ... and {len(empty_files) - 5} more")
    print()

# Show JSON files
if json_files:
    print(f"JSON files ({len(json_files)}) - likely error responses:")
    for f, size in json_files[:5]:
        # Read content to show error
        with open(f, 'rb') as file:
            content = file.read(100).decode('utf-8', errors='ignore')
        print(f"  ❌ {str(f)} - Content: {content[:60]}...")
    if len(json_files) > 5:
        print(f"  ... and {len(json_files) - 5} more")
    print()

# Show invalid files
if invalid_files:
    print(f"Invalid format files ({len(invalid_files)}):")
    for f, size, sig in invalid_files[:5]:
        print(f"  ❌ {str(f)} - Size: {size}, Sig: {sig}")
    if len(invalid_files) > 5:
        print(f"  ... and {len(invalid_files) - 5} more")
    print()

# Overall status
print(f"{'='*70}")
if len(valid_files) == len(resume_files):
    print("✓ SUCCESS: All resume files are valid!")
    sys.exit(0)
else:
    print(f"❌ ISSUE DETECTED: {len(empty_files) + len(json_files) + len(invalid_files)} out of {len(resume_files)} files are problematic")
    
    if json_files:
        print("\nThis suggests Zoho API is returning error responses as files!")
        print("The files are being saved with JSON content instead of binary file content.")
    elif empty_files:
        print("\nEmpty files suggest download is not receiving file content from Zoho.")
    
    sys.exit(1)
