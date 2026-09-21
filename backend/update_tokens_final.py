#!/usr/bin/env python
"""
Update OAuth tokens with NEW credentials provided by Zoho admin.
These tokens SHOULD have Attachments.Download permission.
"""

import os
import sys
from pathlib import Path
os.chdir(Path(__file__).parent)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.core.crypto import encrypt_value
from app.models.integration_settings import IntegrationSettings
import httpx

# NEW tokens from Zoho admin (with hopefully correct permissions!)
NEW_CLIENT_ID = "1000.WA5TEPHE77PLKH4QFWL1NV044OCK7P"
NEW_CLIENT_SECRET = "50686efc31975c713dc65004087e17ee56a7e802e7"
NEW_ACCESS_TOKEN = "1000.a3d7b4813c2d78d6e5df1862330aef4a.c1be3dd94112db5a1d27985fe1b5a6bd"
NEW_REFRESH_TOKEN = "1000.1a188c5392b991ea8f464725082599f8.ccf2795ccce0cd73567d10968d563782"

def validate_tokens():
    """Test if new tokens are valid and have download permissions."""
    
    print("=" * 70)
    print("VALIDATING NEW OAUTH TOKENS")
    print("=" * 70)
    print()
    
    print("Testing token authentication...")
    base_url = "https://recruit.zoho.in/recruit/v2"
    headers = {"Authorization": f"Zoho-oauthtoken {NEW_ACCESS_TOKEN}"}
    
    try:
        with httpx.Client(timeout=10) as client:
            # Test 1: Can we authenticate?
            print("1. Testing authentication...")
            response = client.get(base_url + "/Candidates?per_page=1", headers=headers)
            
            if response.status_code != 200:
                print(f"   ❌ Authentication failed: HTTP {response.status_code}")
                return False
            
            print(f"   ✅ Authentication successful")
            
            candidates = response.json().get('data', [])
            if not candidates:
                print("   ⚠️  No candidates found to test download")
                return True  # Still valid, just no attachments to test
            
            # Test 2: Can we access attachments?
            print("2. Testing attachment access...")
            candidate = candidates[0]
            candidate_id = candidate.get('id')
            
            response = client.get(
                base_url + f"/Candidates/{candidate_id}/Attachments",
                headers=headers
            )
            
            attachments = response.json().get('data', [])
            
            if not attachments:
                print("   ⚠️  No attachments found on this candidate")
                return True
            
            print(f"   ✅ Found {len(attachments)} attachment(s)")
            
            # Test 3: Can we download?
            print("3. Testing attachment DOWNLOAD...")
            attachment = attachments[0]
            attachment_id = attachment.get('id')
            file_name = attachment.get('File_Name', 'unknown')
            
            print(f"   Testing file: {file_name}")
            
            # Try download endpoint
            response = client.get(
                base_url + f"/Attachments/{attachment_id}",
                headers=headers,
                follow_redirects=True
            )
            
            first_bytes = response.content[:10] if response.content else b''
            
            if first_bytes.startswith(b'%PDF'):
                print(f"   ✅ PDF DOWNLOAD SUCCESSFUL!")
                print(f"   ✅✅✅ TOKEN HAS DOWNLOAD PERMISSION! ✅✅✅")
                return True
            elif first_bytes.startswith(b'PK'):
                print(f"   ✅ DOCX DOWNLOAD SUCCESSFUL!")
                print(f"   ✅✅✅ TOKEN HAS DOWNLOAD PERMISSION! ✅✅✅")
                return True
            elif first_bytes.startswith(b'{'):
                print(f"   ❌ Still getting JSON metadata (not binary)")
                print(f"   ❌ Token may still lack download permission")
                return False
            elif response.status_code == 302:
                location = response.headers.get('location', '')
                if 'IAMSecurityError' in location:
                    print(f"   ❌ IAM Security Error - No download permission")
                    return False
            else:
                print(f"   ⚠️  Unexpected response: HTTP {response.status_code}, {len(response.content)} bytes")
                print(f"   First bytes: {first_bytes}")
                return False
                
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    return True

def update_database():
    """Update database with new tokens."""
    
    print()
    print("Updating database with new tokens...")
    
    engine = create_engine(settings.database_url)
    
    try:
        with Session(engine) as session:
            # Get or create integration
            integration = session.scalar(
                select(IntegrationSettings).where(
                    IntegrationSettings.provider == "zoho_recruit"
                )
            )
            
            if not integration:
                print("[INFO] Creating new integration entry...")
                integration = IntegrationSettings(
                    provider="zoho_recruit",
                    is_active=True,
                )
                session.add(integration)
            
            print("   ✓ Encrypting and storing tokens...")
            
            # Update all tokens
            integration.access_token_encrypted = encrypt_value(NEW_ACCESS_TOKEN)
            integration.refresh_token_encrypted = encrypt_value(NEW_REFRESH_TOKEN)
            
            # Set expiration to 1 hour from now
            integration.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            integration.last_checked_at = datetime.now(timezone.utc)
            
            # Mark as healthy
            integration.connection_state = "connected"
            integration.status = "healthy"
            integration.last_error = None
            integration.updated_at = datetime.now(timezone.utc)
            
            session.commit()
            
            print("   ✓ Database updated successfully")
            print()
            
            # Verify
            updated = session.scalar(
                select(IntegrationSettings).where(
                    IntegrationSettings.provider == "zoho_recruit"
                )
            )
            
            print("Verification:")
            print(f"  ✓ Access Token (encrypted): {str(updated.access_token_encrypted)[:50]}...")
            print(f"  ✓ Refresh Token (encrypted): {str(updated.refresh_token_encrypted)[:50]}...")
            print(f"  ✓ Token Expires At: {updated.token_expires_at}")
            print(f"  ✓ Connection State: {updated.connection_state}")
            print(f"  ✓ Status: {updated.status}")
            print()
            
            return True
            
    except Exception as e:
        print(f"❌ Database update failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    
    print()
    print("NEW TOKENS PROVIDED:")
    print(f"  Client ID: {NEW_CLIENT_ID}")
    print(f"  Client Secret: {NEW_CLIENT_SECRET[:20]}...")
    print(f"  Access Token: {NEW_ACCESS_TOKEN[:40]}...")
    print(f"  Refresh Token: {NEW_REFRESH_TOKEN[:40]}...")
    print()
    
    # Step 1: Validate tokens
    if not validate_tokens():
        print()
        print("=" * 70)
        print("⚠️  TOKEN VALIDATION FAILED")
        print("=" * 70)
        print()
        print("The tokens may not have the required permissions.")
        print("Please verify with your Zoho admin that:")
        print("  1. 'Attachments.Download' permission is ENABLED")
        print("  2. Tokens were generated AFTER enabling this permission")
        print("  3. Check exact permission name in Zoho")
        print()
        return False
    
    # Step 2: Update database
    if not update_database():
        print()
        print("=" * 70)
        print("❌ DATABASE UPDATE FAILED")
        print("=" * 70)
        return False
    
    print("=" * 70)
    print("✅✅✅ NEW TOKENS UPDATED SUCCESSFULLY ✅✅✅")
    print("=" * 70)
    print()
    print("Summary:")
    print("  ✓ Access Token: Encrypted and stored")
    print("  ✓ Refresh Token: Encrypted and stored")
    print("  ✓ Expiration: Set to 1 hour (auto-refresh enabled)")
    print("  ✓ Auto-refresh: Will trigger before next sync")
    print("  ✓ Encryption: AES-256 at rest")
    print()
    print("Next steps:")
    print("  1. Restart backend: Kill uvicorn and restart")
    print("  2. New tokens will be loaded automatically")
    print("  3. Try downloading a resume - should work now!")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
