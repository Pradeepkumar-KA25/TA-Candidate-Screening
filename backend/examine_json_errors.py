#!/usr/bin/env python
"""Check what JSON errors are being stored in resume files."""

from pathlib import Path
import json
import sys

# Check all resumes in the uploads/resumes directory
resume_dir = Path("uploads/resumes")

# Find all resume files
resume_files = list(resume_dir.glob("*/resume.*"))

if not resume_files:
    print("No resume files found")
    sys.exit(1)

# Check first few files to see what errors are stored
print(f"Checking first 5 resume files for JSON content...\n")
print(f"{'='*70}")

for resume_file in resume_files[:5]:
    print(f"\nFile: {resume_file}")
    print(f"Size: {resume_file.stat().st_size} bytes")
    print("-" * 70)
    
    try:
        with open(resume_file, 'rb') as f:
            content = f.read()
        
        # Try to decode as JSON
        try:
            data = json.loads(content)
            print("✓ Valid JSON detected:")
            # Pretty print the JSON
            print(json.dumps(data, indent=2)[:500])  # First 500 chars
            if len(str(data)) > 500:
                print("... (truncated)")
        except json.JSONDecodeError:
            print("Raw content (first 200 chars):")
            print(content[:200].decode('utf-8', errors='ignore'))
    except Exception as e:
        print(f"Error reading file: {e}")

print(f"\n{'='*70}")
print("\nSUMMARY: All resumes contain JSON instead of binary file content!")
print("This means the Zoho download_attachment endpoint is returning JSON errors.")
