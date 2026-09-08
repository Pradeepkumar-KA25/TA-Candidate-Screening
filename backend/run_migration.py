#!/usr/bin/env python
"""
Step 8: Attempt migration with full error capture
"""
import subprocess
import sys

def run_migration():
    print("=" * 70)
    print("STEP 8: MIGRATION EXECUTION WITH ERROR CAPTURE")
    print("=" * 70)
    
    print("\nExecuting: python -m alembic upgrade head\n")
    
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        cwd="d:\\Git\\TA Candidate Screening\\backend"
    )
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    
    print(f"\nReturn code: {result.returncode}")
    
    if result.returncode == 0:
        print("\n✓ MIGRATION SUCCESSFUL")
    else:
        print("\n✗ MIGRATION FAILED")
    
    return result.returncode == 0

if __name__ == "__main__":
    import os
    os.chdir("d:\\Git\\TA Candidate Screening\\backend")
    success = run_migration()
    sys.exit(0 if success else 1)
